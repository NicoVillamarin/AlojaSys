import { useMemo, useRef, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import TableGeneric from "src/components/TableGeneric";
import { useList } from "src/hooks/useList";
import { useDispatchAction } from "src/hooks/useDispatchAction";
import fetchWithAuth from "src/services/fetchWithAuth";
import { getApiURL } from "src/services/utils";
import ReservationsModal from "src/components/modals/ReservationsModal";
import MultiRoomReservationsModal from "src/components/modals/MultiRoomReservationsModal";
import MultiRoomReservationDetailModal from "src/components/modals/MultiRoomReservationDetailModal";
import Button from "src/components/Button";
import SelectAsync from "src/components/selects/SelectAsync";
import { Formik } from "formik";
import {
  format,
  parseISO,
  startOfDay,
  isAfter,
  isBefore,
  isSameDay,
} from "date-fns";
import { convertToDecimal, getStatusLabel, RES_STATUS } from "./utils";
import Filter from "src/components/Filter";
import { useUserHotels } from "src/hooks/useUserHotels";
import PaymentModal from "src/components/modals/PaymentModal";
import CancellationModal from "src/components/modals/CancellationModal";
import Badge from "src/components/Badge";
import WhatsappIcon from "src/assets/icons/WhatsappIcon";
import { useAuthStore } from "src/stores/useAuthStore";
import AutoNoShowButton from "src/components/AutoNoShowButton";
import AlertSwal from "src/components/AlertSwal";
import EditIcon from "src/assets/icons/EditIcon";
import ConfirmIcon from "src/assets/icons/ConfirmIcon";
import CheckinIcon from "src/assets/icons/CheckinIcon";
import CheckoutIcon from "src/assets/icons/CheckoutIcon";
import CancelIcon from "src/assets/icons/CancelIcon";
import InvoiceIcon from "src/assets/icons/InvoiceIcon";
import EarlyCheckoutIcon from "src/assets/icons/EarlyCheckoutIcon";
import CheckCircleIcon from "src/assets/icons/CheckCircleIcon";
import CheckIcon from "src/assets/icons/CheckIcon";
import InvoiceStatus from "src/components/reservations/InvoiceStatus";
import PaymentTooltip from "src/components/reservations/PaymentTooltip";
import PaymentStatusBadge from "src/components/reservations/PaymentStatusBadge";
import Tooltip from "src/components/Tooltip";
import { Chevron } from "src/assets/icons/Chevron";
import { useEffectOnce } from "src/hooks/useEffectOnce";
import { usePermissions, useHasAnyPermission } from "src/hooks/usePermissions";
import ActionMenuButton from "src/components/ActionMenuButton";
import { exportJsonToExcel } from "src/utils/exportExcel";
import { showErrorConfirm, showSuccess } from "src/services/toast";
import GuestDetailsModal from "src/components/modals/GuestDetailsModal";
import PrintIcon from "src/assets/icons/PrintIcon";
import SaveIcon from "src/assets/icons/SaveIcon";
import { printHtml } from "src/utils/printHtml";

export default function ReservationsGestions() {
  const { t, i18n } = useTranslation();
  
  // Verificar permisos CRUD para reservas
  const canViewReservation = usePermissions("reservations.view_reservation");
  const canAddReservation = usePermissions("reservations.add_reservation");
  const canChangeReservation = usePermissions("reservations.change_reservation");
  const canDeleteReservation = usePermissions("reservations.delete_reservation");
  const canAddPayment = usePermissions("reservations.add_payment");
  const canAddInvoice = usePermissions("invoicing.add_invoice");
  const [showModal, setShowModal] = useState(false);
  const [showMultiCreateModal, setShowMultiCreateModal] = useState(false);
  const [showCreateTypeMenu, setShowCreateTypeMenu] = useState(false);
  const [editReservation, setEditReservation] = useState(null);
  // Modal Facturación (selección de condición IVA)
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [invoiceReservation, setInvoiceReservation] = useState(null);
  const [selectedTaxCondition, setSelectedTaxCondition] = useState("5"); // 5 = Consumidor Final
  const [selectedDocType, setSelectedDocType] = useState("80"); // 80 = CUIT, 96 = DNI, 99 = CF
  const [selectedDocNumber, setSelectedDocNumber] = useState("");
  const [isCreatingInvoice, setIsCreatingInvoice] = useState(false);
  const [payOpen, setPayOpen] = useState(false);
  const [payReservationId, setPayReservationId] = useState(null);
  const [balancePayOpen, setBalancePayOpen] = useState(false);
  const [balancePayReservationId, setBalancePayReservationId] = useState(null);
  const [balanceInfo, setBalanceInfo] = useState(null);
  const [pendingAction, setPendingAction] = useState(null); // 'check_in' o 'check_out'
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReservation, setCancelReservation] = useState(null);
  const [showEarlyCheckOutAlert, setShowEarlyCheckOutAlert] = useState(false);
  const [earlyCheckOutReservation, setEarlyCheckOutReservation] =
    useState(null);
  const [showSuccessAlert, setShowSuccessAlert] = useState(false);
  const [successData, setSuccessData] = useState(null);
  const [showInfoAlert, setShowInfoAlert] = useState(false);
  const [infoData, setInfoData] = useState(null);
  const [showMultiRoomDetail, setShowMultiRoomDetail] = useState(false);
  const [selectedMultiRoomGroup, setSelectedMultiRoomGroup] = useState(null);
  const [editMultiRoomGroup, setEditMultiRoomGroup] = useState(null);
  const [multiRoomRefreshKey, setMultiRoomRefreshKey] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [isPrinting, setIsPrinting] = useState(false);
  const [guestDetailsOpen, setGuestDetailsOpen] = useState(false);
  const [guestDetailsReservation, setGuestDetailsReservation] = useState(null);
  const [filters, setFilters] = useState({
    search: "",
    hotel: "",
    room: "",
    status: "",
    dateFrom: "",
    dateTo: "",
  });
  const didMountRef = useRef(false);
  const {
    hotelIdsString,
    isSuperuser,
    hotelIds,
    hasSingleHotel,
    singleHotelId,
  } = useUserHotels();
  const { results, isPending, hasNextPage, fetchNextPage, refetch } = useList({
    resource: "reservations",
    params: {
      search: filters.search,
      hotel: filters.hotel || undefined,
      room: filters.room || undefined,
      status: filters.status || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      ordering: "-id", // Ordenar por ID descendente (más recientes primero), con ordenamiento secundario por check_in en backend
      page_size: 1000, // Cargar más resultados para evitar problemas de paginación
    },
    enabled: canViewReservation, // Solo cargar datos si tiene permiso para ver reservas
  });

  // Obtener lista de hoteles para verificar configuración
  const { results: hotels } = useList({
    resource: "hotels",
    params: !isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {},
  });

  // Obtener información del hotel seleccionado para verificar configuración
  const selectedHotel =
    hotels?.find((h) => String(h.id) === String(filters.hotel)) ||
    (hasSingleHotel ? hotels?.[0] : null);

  // Verificar si el hotel tiene auto no-show habilitado
  const hasAutoNoShowEnabled = selectedHotel?.auto_no_show_enabled || false;

  const { mutate: doAction, isPending: acting } = useDispatchAction({
    resource: "reservations",
    onSuccess: () => refetch(),
  });

  const displayResults = useMemo(() => {
    const q = (filters.search || "").trim().toLowerCase();
    let arr = results || [];

    // Excluir reservas finalizadas (check_out) de la gestión
    // No filtramos por fecha aquí - las reservas pueden haberse creado hace tiempo pero aún no haber llegado el check-in
    arr = arr.filter(
      (r) =>
        r.status !== "check_out" &&
        r.status !== "cancelled" &&
        r.status !== "no_show"
    );

    if (q) {
      arr = arr.filter((r) => {
        const guest = String(r.guest_name ?? "").toLowerCase();
        const hotel = String(r.hotel_name ?? "").toLowerCase();
        const room = String(r.room_name ?? "").toLowerCase();
        const status = String(r.status ?? "").toLowerCase();
        const group = String(r.group_code ?? "").toLowerCase();
        return (
          guest.includes(q) ||
          hotel.includes(q) ||
          room.includes(q) ||
          status.includes(q) ||
          group.includes(q)
        );
      });
    }

    // Agrupar por group_code para reservas multi-habitación
    const groupedByCode = {};
    const singles = [];
    for (const r of arr) {
      if (r.group_code) {
        if (!groupedByCode[r.group_code]) groupedByCode[r.group_code] = [];
        groupedByCode[r.group_code].push(r);
      } else {
        singles.push(r);
      }
    }

    const groupRows = [];
    Object.values(groupedByCode).forEach((group) => {
      if (group.length === 1) {
        // Grupo de una sola habitación: se muestra como reserva normal
        singles.push(group[0]);
        return;
      }
      const first = group[0];
      const roomsCount = group.length;
      const totalPrice = group.reduce(
        (sum, item) => sum + (parseFloat(item.total_price) || 0),
        0
      );
      const totalGuests = group.reduce(
        (sum, item) => sum + (parseInt(item.guests) || 0),
        0
      );

      groupRows.push({
        ...first,
        // Meta para UI
        is_group: true,
        group_reservations: group,
        rooms_count: roomsCount,
        // Sobrescribir campos que queremos mostrar agregados
        total_price: totalPrice,
        guests: totalGuests,
      });
    });

    const finalArr = [...singles, ...groupRows];

    // Ordenar por ID descendente por defecto (más recientes primero)
    finalArr.sort((a, b) => (b.id || 0) - (a.id || 0));
    return finalArr;
  }, [results, filters.search]);

  const normalizeReservationForExport = (r, { groupCode = "", isFromGroup = false } = {}) => {
    const isOta = r?.is_ota || r?.external_id;
    const channel = r?.channel_display || r?.channel || (isOta ? "OTA" : "Directo");

    const safeDate = (value, fmt) => {
      if (!value) return "";
      try {
        return format(parseISO(value), fmt);
      } catch {
        return String(value);
      }
    };

    return {
      ID: r?.id ?? "",
      Reserva: r?.display_name ?? "",
      Huésped: r?.guest_name ?? "",
      Hotel: r?.hotel_name ?? "",
      Habitación: r?.room_name ?? "",
      Canal: channel,
      "Check-in": safeDate(r?.check_in, "dd/MM/yyyy"),
      "Check-out": safeDate(r?.check_out, "dd/MM/yyyy"),
      Creada: safeDate(r?.created_at, "dd/MM/yyyy HH:mm"),
      Huéspedes: r?.guests ?? "",
      Total: typeof r?.total_price === "number" ? r.total_price : (parseFloat(r?.total_price) || 0),
      Estado: getStatusLabel(r?.status, t),
      "Pagada por": r?.paid_by || "",
      "Total pagado": typeof r?.total_paid === "number" ? r.total_paid : (parseFloat(r?.total_paid) || 0),
      "Saldo pendiente": typeof r?.balance_due === "number" ? r.balance_due : (parseFloat(r?.balance_due) || 0),
      Grupo: groupCode || r?.group_code || "",
      "Multi-habitación": isFromGroup ? "Sí" : "No",
      Overbooking: r?.overbooking_flag ? "Sí" : "No",
    };
  };

  const handleExportExcel = async () => {
    if (!displayResults?.length) {
      showErrorConfirm("No hay reservas para exportar con los filtros actuales.");
      return;
    }

    try {
      setIsExporting(true);
      const rows = [];
      for (const r of displayResults) {
        if (r?.is_group && Array.isArray(r.group_reservations) && r.group_reservations.length > 0) {
          for (const rr of r.group_reservations) {
            rows.push(
              normalizeReservationForExport(rr, {
                groupCode: r.group_code || "",
                isFromGroup: true,
              })
            );
          }
        } else {
          rows.push(
            normalizeReservationForExport(r, {
              groupCode: r?.group_code || "",
              isFromGroup: false,
            })
          );
        }
      }

      const today = format(new Date(), "yyyy-MM-dd");
      await exportJsonToExcel({
        rows,
        filename: `reservas_gestion_${today}.xlsx`,
        sheetName: "Reservas",
      });
      showSuccess("Excel generado correctamente.");
    } catch (error) {
      console.error("Error exportando reservas:", error);
      showErrorConfirm("No se pudo exportar el Excel. Revisá la consola para más detalle.");
    } finally {
      setIsExporting(false);
    }
  };

  const handlePrintGuestCard = async (reservation) => {
    try {
      // Obtener datos completos del hotel (incluyendo políticas)
      const hotelData = hotels?.find((h) => String(h.id) === String(reservation.hotel)) || null;
      if (!hotelData) {
        showErrorConfirm("No se encontró información del hotel.");
        return;
      }

      // Obtener datos del huésped principal
      const primaryGuest = reservation.guests_data?.find((g) => g.is_primary) || reservation.guests_data?.[0] || null;
      const guestName = primaryGuest?.name || reservation.guest_name || "Huésped";
      const guestEmail = primaryGuest?.email || "";
      const guestPhone = primaryGuest?.phone || "";

      const cardTitle = "Ficha del Pasajero";
      const printTitle = "Ficha"; // Título corto para la pestaña (evita duplicar en header de impresión)
      const now = new Date();
      const nowStr = format(now, "dd/MM/yyyy HH:mm");

      const escapeHtml = (input) =>
        String(input ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");

      const checkInDate = reservation.check_in
        ? format(parseISO(reservation.check_in), "dd/MM/yyyy")
        : "";
      const checkOutDate = reservation.check_out
        ? format(parseISO(reservation.check_out), "dd/MM/yyyy")
        : "";
      const checkInTime = hotelData.check_in_time || "15:00";
      const checkOutTime = hotelData.check_out_time || "11:00";

      const nights = reservation.check_in && reservation.check_out
        ? Math.ceil(
            (new Date(reservation.check_out) - new Date(reservation.check_in)) /
              (1000 * 60 * 60 * 24)
          )
        : 0;

      const html = `
        <div style="max-width: 800px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column;">
          <div style="flex: 1;">
            <h1 style="text-align: center; margin-bottom: 24px; font-size: 20px; font-weight: 700; color: #111827;">${escapeHtml(cardTitle)}</h1>
            
            <div style="margin-bottom: 24px;">
              <h2 style="font-size: 16px; font-weight: 600; margin-bottom: 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px;">
                Datos del Huésped
              </h2>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px; font-weight: 600; width: 180px;">Nombre:</td>
                <td style="padding: 8px;">${escapeHtml(guestName)}</td>
              </tr>
              ${guestEmail ? `
              <tr>
                <td style="padding: 8px; font-weight: 600;">Email:</td>
                <td style="padding: 8px;">${escapeHtml(guestEmail)}</td>
              </tr>
              ` : ""}
              ${guestPhone ? `
              <tr>
                <td style="padding: 8px; font-weight: 600;">Teléfono:</td>
                <td style="padding: 8px;">${escapeHtml(guestPhone)}</td>
              </tr>
              ` : ""}
              <tr>
                <td style="padding: 8px; font-weight: 600;">Huéspedes:</td>
                <td style="padding: 8px;">${escapeHtml(reservation.guests || 1)}</td>
              </tr>
            </table>
          </div>

          <div style="margin-bottom: 24px;">
            <h2 style="font-size: 16px; font-weight: 600; margin-bottom: 12px; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px;">
              Información de la Reserva
            </h2>
            <table style="width: 100%; border-collapse: collapse;">
              <tr>
                <td style="padding: 8px; font-weight: 600; width: 180px;">Número de Reserva:</td>
                <td style="padding: 8px;">#${escapeHtml(reservation.id || "")}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Hotel:</td>
                <td style="padding: 8px;">${escapeHtml(reservation.hotel_name || hotelData.name || "")}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Habitación:</td>
                <td style="padding: 8px;">${escapeHtml(reservation.room_name || "")}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Fecha de Llegada:</td>
                <td style="padding: 8px;">${escapeHtml(checkInDate)} - Check-in: ${escapeHtml(checkInTime)}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Fecha de Salida:</td>
                <td style="padding: 8px;">${escapeHtml(checkOutDate)} - Check-out: ${escapeHtml(checkOutTime)}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Noches:</td>
                <td style="padding: 8px;">${escapeHtml(nights)}</td>
              </tr>
              <tr>
                <td style="padding: 8px; font-weight: 600;">Tarifa Total:</td>
                <td style="padding: 8px; font-size: 16px; font-weight: 700;">$ ${escapeHtml(convertToDecimal(reservation.total_price || 0))}</td>
              </tr>
              ${reservation.total_paid > 0 ? `
              <tr>
                <td style="padding: 8px; font-weight: 600;">Total Pagado:</td>
                <td style="padding: 8px;">$ ${escapeHtml(convertToDecimal(reservation.total_paid || 0))}</td>
              </tr>
              ` : ""}
              ${(reservation.balance_due || 0) > 0 ? `
              <tr>
                <td style="padding: 8px; font-weight: 600;">Saldo Pendiente:</td>
                <td style="padding: 8px; font-weight: 700;">$ ${escapeHtml(convertToDecimal(reservation.balance_due || 0))}</td>
              </tr>
              ` : ""}
            </table>
          </div>

            ${hotelData.guest_card_policies ? `
            <div style="margin-top: 32px; padding-top: 24px; border-top: 2px solid #e5e7eb;">
              <h2 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">
                Políticas y Horarios del Hotel
              </h2>
              <div style="white-space: pre-wrap; line-height: 1.6; color: #374151;">
                ${escapeHtml(hotelData.guest_card_policies)}
              </div>
            </div>
            ` : ""}
          </div>

          <div style="margin-top: auto; padding-top: 32px; border-top: 1px solid #e5e7eb;">
            <div style="text-align: center; margin-bottom: 8px;">
              <div style="border-top: 1px solid #111827; width: 300px; margin: 0 auto 8px;"></div>
              <div style="font-size: 14px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                Firma del Pasajero
              </div>
            </div>
            <div style="text-align: center; font-size: 11px; color: #6b7280; padding-bottom: 0;">
              Ficha generada el ${escapeHtml(nowStr)}
            </div>
          </div>
        </div>
      `;

      printHtml({ title: printTitle, html });
    } catch (e) {
      showErrorConfirm(e?.message || String(e) || "No se pudo imprimir la ficha del pasajero.");
    }
  };

  const handlePrint = () => {
    if (!displayResults?.length) {
      showErrorConfirm("No hay reservas para imprimir con los filtros actuales.");
      return;
    }

    try {
      setIsPrinting(true);
      const today = format(new Date(), "dd/MM/yyyy HH:mm");
      const title = "Reservas (Gestión)";

      // Expandir grupos (imprimir una fila por habitación/reserva real)
      const rows = [];
      for (const r of displayResults) {
        if (r?.is_group && Array.isArray(r.group_reservations) && r.group_reservations.length > 0) {
          for (const rr of r.group_reservations) {
            rows.push(
              normalizeReservationForExport(rr, {
                groupCode: r.group_code || "",
                isFromGroup: true,
              })
            );
          }
        } else {
          rows.push(
            normalizeReservationForExport(r, {
              groupCode: r?.group_code || "",
              isFromGroup: false,
            })
          );
        }
      }

      const escapeHtml = (input) =>
        String(input ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");

      const html = `
        <h1 class="title">${escapeHtml(title)}</h1>
        <div class="meta">
          <span class="badge">${escapeHtml(today)}</span>
          <span class="badge" style="margin-left:8px;">${escapeHtml(
            `${rows.length} registros`
          )}</span>
        </div>
        <table>
          <thead>
            <tr>
              <th style="width:70px;">ID</th>
              <th>Huésped</th>
              <th>Hotel</th>
              <th>Habitación</th>
              <th style="width:110px;">Check-in</th>
              <th style="width:110px;">Check-out</th>
              <th class="center" style="width:80px;">Huéspedes</th>
              <th class="right" style="width:110px;">Total</th>
              <th style="width:140px;">Estado</th>
              <th style="width:140px;">Grupo</th>
            </tr>
          </thead>
          <tbody>
            ${rows
              .map((r) => {
                const total = typeof r?.Total === "number" ? r.Total : parseFloat(r?.Total || 0) || 0;
                return `
                  <tr>
                    <td class="center">${escapeHtml(r?.ID ?? "")}</td>
                    <td>${escapeHtml(r?.Huésped ?? "")}</td>
                    <td>${escapeHtml(r?.Hotel ?? "")}</td>
                    <td>${escapeHtml(r?.Habitación ?? "")}</td>
                    <td>${escapeHtml(r?.["Check-in"] ?? "")}</td>
                    <td>${escapeHtml(r?.["Check-out"] ?? "")}</td>
                    <td class="center">${escapeHtml(r?.Huéspedes ?? "")}</td>
                    <td class="right">$ ${escapeHtml(convertToDecimal(total))}</td>
                    <td>${escapeHtml(r?.Estado ?? "")}</td>
                    <td>${escapeHtml(r?.Grupo ?? "")}</td>
                  </tr>
                `;
              })
              .join("")}
          </tbody>
        </table>
      `;

      printHtml({ title, html });
    } catch (e) {
      showErrorConfirm(e?.message || String(e) || "No se pudo imprimir.");
    } finally {
      setIsPrinting(false);
    }
  };

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    const id = setTimeout(() => refetch(), 400);
    return () => clearTimeout(id);
  }, [filters.search, filters.hotel, filters.room, filters.status, filters.dateFrom, filters.dateTo, refetch]);

  // Escuchar eventos SSE de OTAs para refrescar automáticamente al recibir cambios
  useEffect(() => {
    const base = getApiURL();
    const hotelParam = filters.hotel ? `?hotel=${filters.hotel}` : "";
    const es = new EventSource(`${base}/api/otas/events/stream/${hotelParam}`);
    es.onmessage = () => {
      refetch();
    };
    es.addEventListener("update", () => refetch());
    es.addEventListener("ping", () => {});
    es.onerror = () => {
      try {
        es.close();
      } catch {}
      // Reintento simple después de 3s
      setTimeout(() => {
        // noop, el próximo render volverá a crear el EventSource
      }, 3000);
    };
    return () => {
      try {
        es.close();
      } catch {}
    };
  }, [filters.hotel, refetch]);

  const hasOverbooking = (r) => !!r.overbooking_flag;
  const isOtaReservation = (r) => {
    const ext = r?.external_id;
    if (ext !== null && typeof ext !== "undefined" && String(ext).trim() !== "") return true;
    // Algunos clients podrían serializar booleans como string
    if (r?.is_ota === true) return true;
    if (String(r?.is_ota).toLowerCase() === "true") return true;
    return false;
  };
  const isOtaChannel = (r) => {
    const ch = String(r?.channel || "").toLowerCase().trim();
    // Canales OTA conocidos (ver ReservationChannel en backend)
    return ch === "booking" || ch === "airbnb" || ch === "expedia" || ch === "other";
  };
  const canCheckIn = (r) => 
    canChangeReservation && 
    r.status === "confirmed" && 
    !hasOverbooking(r);

  // Check-out normal: solo disponible en o después de la fecha de check-out
  const canCheckOut = (r) => {
    if (!canChangeReservation) return false;
    if (r.status !== "check_in" || hasOverbooking(r)) return false;
    if (!r.check_out) return false;

    try {
      const today = startOfDay(new Date());
      const checkoutDate = startOfDay(parseISO(r.check_out));
      // Solo disponible si hoy es >= fecha de check-out (mismo día o después)
      return isSameDay(today, checkoutDate) || isAfter(today, checkoutDate);
    } catch (error) {
      console.error("Error comparando fechas en canCheckOut:", error);
      return false;
    }
  };

  // Salida anticipada: solo disponible antes de la fecha de check-out
  const canEarlyCheckOut = (r) => {
    if (!canChangeReservation) return false;
    if (r.status !== "check_in" || hasOverbooking(r)) return false;
    if (!r.check_out) return false;

    try {
      const today = startOfDay(new Date());
      const checkoutDate = startOfDay(parseISO(r.check_out));
      // Solo disponible si hoy es < fecha de check-out (antes del día de salida)
      return isBefore(today, checkoutDate);
    } catch (error) {
      console.error("Error comparando fechas en canEarlyCheckOut:", error);
      return false;
    }
  };

  const canCancel = (r) =>
    canDeleteReservation &&
    !isOtaReservation(r) &&
    !isOtaChannel(r) &&
    (r.status === "pending" || r.status === "confirmed");
  const canConfirm = (r) => 
    canAddPayment && 
    r.status === "pending" && 
    !hasOverbooking(r);
  const canEdit = (r) => 
    canChangeReservation && 
    (r.status === "pending" || hasOverbooking(r)); // Editar permitido si pendiente o si hay overbooking para resolver

  // Función para determinar si se puede generar factura
  const canGenerateInvoice = (r) => {
    // Solo se puede generar factura si:
    // 1. Tiene permiso para crear facturas
    // 2. La reserva está confirmada o en check-in/check-out
    // 3. Tiene precio total > 0
    // 4. No tiene facturas existentes (esto se verifica en el componente InvoiceStatus)
    return (
      canAddInvoice &&
      (r.status === "confirmed" ||
        r.status === "check_in" ||
        r.status === "check_out") &&
      r.total_price > 0 &&
      !hasOverbooking(r)
    );
  };

  // Función para determinar el tipo de documento a generar
  const getDocumentType = (r) => {
    const balance = r.balance_due || 0;
    const totalPaid = r.total_paid || 0;
    const totalPrice = r.total_price || 0;
    const isFullyPaid = balance <= 0.01;
    const hasPartialPayments = totalPaid > 0 && !isFullyPaid;

    if (isFullyPaid) {
      return "invoice"; // Factura completa
    } else if (hasPartialPayments) {
      return "receipt"; // Comprobante de seña/pago parcial
    } else {
      return "none"; // Sin pagos
    }
  };

  // Función para obtener el mensaje de cancelación según el estado
  const getCancelMessage = (r) => {
    if (r.status === "pending") {
      return t("dashboard.reservations_management.actions.cancel_free");
    } else if (r.status === "confirmed") {
      return t("dashboard.reservations_management.actions.cancel_with_policy");
    }
    return t("dashboard.reservations_management.actions.cancel");
  };

  // Función para obtener el tooltip de cancelación
  const getCancelTooltip = (r) => {
    if (r.status === "pending") {
      return t("dashboard.reservations_management.tooltips.cancel_free");
    } else if (r.status === "confirmed") {
      return t("dashboard.reservations_management.tooltips.cancel_with_policy");
    }
    return "";
  };

  // Función helper para mostrar mensajes de éxito
  const showSuccessMessage = (title, description) => {
    setSuccessData({ title, description });
    setShowSuccessAlert(true);
  };

  // Función helper para mostrar mensajes de información
  const showInfoMessage = (
    title,
    description,
    tone = "info",
    onConfirm = null
  ) => {
    setInfoData({ title, description, tone, onConfirm });
    setShowInfoAlert(true);
  };

  const onCheckIn = async (r) => {

    try {
      const token = useAuthStore.getState().accessToken;
      const response = await fetch(
        `${getApiURL()}/api/reservations/${r.id}/check_in/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        }
      );

      const data = await response.json();

      if (response.status === 402 && data.requires_payment) {
        // Mostrar modal de pago de saldo pendiente
        setBalancePayReservationId(r.id);
        setBalanceInfo({
          balance_due: data.balance_due,
          total_paid: data.total_paid,
          total_reservation: data.total_reservation,
          payment_required_at: data.payment_required_at,
        });
        setPendingAction("check_in");
        setBalancePayOpen(true);
      } else if (response.ok) {
        // Check-in exitoso, refrescar datos y mostrar mensaje
        refetch();
        showSuccessMessage(
          "Check-in Exitoso",
          `La reserva #${r.id} de ${r.guest_name} ha sido registrada como check-in exitosamente.`
        );
      } else {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Error en check-in:", error);
      // Si hay error, intentar con el método original
      doAction({ action: `${r.id}/check_in`, body: {}, method: "POST" });
    }
  };

  const onCheckOut = async (r) => {

    try {
      const token = useAuthStore.getState().accessToken;
      const response = await fetch(
        `${getApiURL()}/api/reservations/${r.id}/check_out/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        }
      );

      const data = await response.json();

      if (response.status === 402 && data.requires_payment) {
        // Mostrar modal de pago de saldo pendiente
        setBalancePayReservationId(r.id);
        setBalanceInfo({
          balance_due: data.balance_due,
          total_paid: data.total_paid,
          total_reservation: data.total_reservation,
          payment_required_at: data.payment_required_at,
        });
        setPendingAction("check_out");
        setBalancePayOpen(true);
      } else if (response.ok) {
        // Check-out exitoso, refrescar datos y mostrar mensaje
        refetch();
        showSuccessMessage(
          "Check-out Exitoso",
          `La reserva #${r.id} de ${r.guest_name} ha sido registrada como check-out exitosamente.`
        );
      } else {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Error en check-out:", error);
      // Si hay error, intentar con el método original
      doAction({ action: `${r.id}/check_out`, body: {}, method: "POST" });
    }
  };
  const onCancel = (r) => {
    setCancelReservation(r);
    setCancelModalOpen(true);
  };
  const onConfirm = (r) => {
    // Abrir modal de pago antes de confirmar
    setPayReservationId(r.id);
    setPayOpen(true);
  };
  const onEdit = async (r) => {
    
    // Detectar si es una reserva multi-habitación
    if (r.is_group && r.group_code && r.group_reservations && r.group_reservations.length > 1) {
      // Es multi-habitación: abrir modal de edición multi-habitación
      setEditMultiRoomGroup({
        groupCode: r.group_code,
        groupReservations: r.group_reservations,
      });
    } else if (r.group_code) {
      // Tiene group_code pero no está agrupado en displayResults
      // Buscar todas las reservas del grupo
      try {
        const response = await fetchWithAuth(
          `${getApiURL()}/api/reservations/?group_code=${r.group_code}`,
          { method: "GET" }
        );
        if (response && Array.isArray(response.results) && response.results.length > 1) {
          setEditMultiRoomGroup({
            groupCode: r.group_code,
            groupReservations: response.results,
          });
          return;
        }
      } catch (error) {
        console.error("Error buscando reservas del grupo:", error);
      }
      // Si falla o solo hay una, tratar como reserva simple
      setEditReservation(r);
    } else {
      // Es reserva simple: abrir modal de edición normal
      setEditReservation(r);
    }
  };

  const onEarlyCheckOut = (r) => {
    // Guardar la reserva y mostrar el modal de confirmación
    setEarlyCheckOutReservation(r);
    setShowEarlyCheckOutAlert(true);
  };

  const onGenerateInvoice = async (r) => {

    // Verificar si ya existe una factura para esta reserva
    try {
      const existingInvoices = await fetchWithAuth(
        `${getApiURL()}/api/invoicing/invoices/by-reservation/${r.id}/`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      // Verificar si hay facturas en la respuesta
      const invoices = existingInvoices || [];
      if (invoices && invoices.length > 0) {
        showInfoMessage(
          "Factura ya existe",
          `Ya existe una factura para esta reserva: ${invoices[0].number}`,
          "warning"
        );
        return;
      }
    } catch (error) {
      // Si hay error en la verificación, continuar con la creación
    }

    // Abrir modal para capturar condición IVA / documento
    setInvoiceReservation(r);
    setSelectedTaxCondition("5");
    setSelectedDocType("80");
    setSelectedDocNumber("");
    setShowInvoiceModal(true);
  };

  const onGenerateReceipt = async (r) => {

    try {
      // Obtener los pagos de la reserva
      const payments = await fetchWithAuth(
        `${getApiURL()}/api/reservations/${r.id}/payments/`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!payments || payments.length === 0) {
        showInfoMessage(
          "Sin Pagos",
          "No hay pagos para mostrar comprobante",
          "warning"
        );
        return;
      }

      // Tomar el último pago parcial (seña). Fallback heurístico si falta is_deposit
      const totalPrice = parseFloat(r.total_price || 0);
      const candidateDeposits = payments.filter((p) => p.is_deposit === true);
      const heuristicDeposits = payments.filter(
        (p) => parseFloat(p.amount || 0) + 0.01 < totalPrice
      );
      const deposits = (
        candidateDeposits.length ? candidateDeposits : heuristicDeposits
      ).sort((a, b) => new Date(b.date) - new Date(a.date));
      const lastDeposit = deposits[0];
      if (!lastDeposit) {
        showInfoMessage(
          "Sin Señas",
          "No hay pagos de seña para mostrar comprobante",
          "warning"
        );
        return;
      }

      // Verificar si ya existe un comprobante generado
      if (lastDeposit.receipt_pdf_url) {
        // Construir URL completa si es relativa
        let pdfUrl = lastDeposit.receipt_pdf_url;
        if (pdfUrl.startsWith("/media/")) {
          // Si es una URL relativa, construir la URL absoluta usando el backend
          pdfUrl = `${getApiURL()}${pdfUrl}`;
        }
        // Abrir el PDF directamente
        window.open(pdfUrl, "_blank");
      } else {
        // Si no existe, solicitarlo y abrir después
        showInfoMessage(
          "Generando Comprobante",
          "El comprobante se está generando. Se abrirá en unos momentos.",
          "info"
        );

        const resp = await fetchWithAuth(
          `${getApiURL()}/api/payments/generate-receipt/${lastDeposit.id}/`,
          {
            method: "POST",
          }
        );

        if (resp?.receipt_pdf_url) {
          // Construir URL completa si es relativa
          let pdfUrl = resp.receipt_pdf_url;
          if (pdfUrl.startsWith("/media/")) {
            // Si es una URL relativa, construir la URL absoluta usando el backend
            pdfUrl = `${getApiURL()}${pdfUrl}`;
          }
          // Esperar un momento y abrir el PDF
          setTimeout(() => {
            window.open(pdfUrl, "_blank");
          }, 2000);
        } else {
          showInfoMessage(
            "Comprobante en Proceso",
            "El comprobante se está generando. Intenta abrirlo nuevamente en unos segundos.",
            "info"
          );
        }
      }
    } catch (error) {
      console.error("Error abriendo comprobante:", error);
      showInfoMessage(
        "Error",
        `Error abriendo comprobante: ${error.message || "Error desconocido"}`,
        "danger"
      );
    }
  };

  const handleEarlyCheckOutConfirm = async () => {
    if (!earlyCheckOutReservation) return;

    const r = earlyCheckOutReservation;

    try {
      const token = useAuthStore.getState().accessToken;
      const response = await fetch(
        `${getApiURL()}/api/reservations/${r.id}/check_out/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        }
      );

      const data = await response.json();

      if (response.status === 402 && data.requires_payment) {
        // Mostrar modal de pago de saldo pendiente
        setBalancePayReservationId(r.id);
        setBalanceInfo({
          balance_due: data.balance_due,
          total_paid: data.total_paid,
          total_reservation: data.total_reservation,
          payment_required_at: data.payment_required_at,
        });
        setPendingAction("check_out");
        setBalancePayOpen(true);
      } else if (response.ok) {
        // Early check-out exitoso, refrescar datos y mostrar mensaje
        refetch();
        showSuccessMessage(
          "Check-out Temprano Exitoso",
          `La reserva #${r.id} de ${r.guest_name} ha sido registrada como check-out temprano exitosamente.`
        );
      } else {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error("Error en early check-out:", error);
      // Si hay error, intentar con el método original
      doAction({ action: `${r.id}/check_out`, body: {}, method: "POST" });
    } finally {
      // Cerrar el modal
      setShowEarlyCheckOutAlert(false);
      setEarlyCheckOutReservation(null);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">
            {t("dashboard.reservations_management.title")}
          </div>
          <h1 className="text-2xl font-semibold text-aloja-navy">
            {t("dashboard.reservations_management.subtitle")}
          </h1>
        </div>
        <div className="flex gap-3">
          <ActionMenuButton
            label="Exportar"
            variant="success"
            size="md"
            isPending={isExporting || isPrinting}
            loadingText={isExporting ? "Exportando..." : "Preparando..."}
            items={[
              {
                key: "excel",
                label: "Exportar a Excel",
                onClick: handleExportExcel,
                disabled: isExporting || isPrinting,
                leftIcon: <SaveIcon size="18" />,
              },
              {
                key: "print",
                label: "Imprimir",
                onClick: handlePrint,
                disabled: isExporting || isPrinting,
                leftIcon: <PrintIcon size={18} />,
              },
            ]}
          />
          <AutoNoShowButton
            selectedHotel={selectedHotel}
            hasAutoNoShowEnabled={hasAutoNoShowEnabled}
            onSuccess={refetch}
          />
          {canAddReservation && (
            <div className="relative">
              <Button
                variant="primary"
                size="md"
                onClick={() => setShowCreateTypeMenu((prev) => !prev)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-white">
                    <Chevron open={showCreateTypeMenu} />
                  </span>
                  <span>
                    {t("dashboard.reservations_management.create_reservation")}
                  </span>
                </div>
              </Button>
              {showCreateTypeMenu && (
                <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                  <button
                    type="button"
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 cursor-pointer"
                    onClick={() => {
                      setShowCreateTypeMenu(false);
                      setShowModal(true);
                    }}
                  >
                    {t(
                      "dashboard.reservations_management.create_simple_reservation",
                      "Reserva simple"
                    )}
                  </button>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 border-t border-gray-100 cursor-pointer"
                    onClick={() => {
                      setShowCreateTypeMenu(false);
                      setShowMultiCreateModal(true);
                    }}
                  >
                    {t(
                      "dashboard.reservations_management.create_multi_room_reservation",
                      "Reserva multi-habitaciones"
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <ReservationsModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={refetch}
      />
      <ReservationsModal
        isOpen={!!editReservation}
        onClose={() => setEditReservation(null)}
        isEdit={true}
        reservation={editReservation}
        onSuccess={refetch}
      />
      <MultiRoomReservationsModal
        isOpen={showMultiCreateModal}
        onClose={() => setShowMultiCreateModal(false)}
        onSuccess={refetch}
        refreshKey={multiRoomRefreshKey}
      />
      <MultiRoomReservationsModal
        isOpen={!!editMultiRoomGroup}
        onClose={() => setEditMultiRoomGroup(null)}
        onSuccess={refetch}
        isEdit={true}
        groupCode={editMultiRoomGroup?.groupCode}
        groupReservations={editMultiRoomGroup?.groupReservations}
        refreshKey={multiRoomRefreshKey}
      />

      <MultiRoomReservationDetailModal
        isOpen={showMultiRoomDetail}
        onClose={() => {
          setShowMultiRoomDetail(false);
          setSelectedMultiRoomGroup(null);
        }}
        groupCode={selectedMultiRoomGroup?.groupCode}
        groupReservations={selectedMultiRoomGroup?.groupReservations}
      />

      <GuestDetailsModal
        isOpen={guestDetailsOpen}
        onClose={() => {
          setGuestDetailsOpen(false);
          setGuestDetailsReservation(null);
        }}
        reservation={guestDetailsReservation}
      />

      <PaymentModal
        isOpen={payOpen}
        reservationId={payReservationId}
        onClose={() => setPayOpen(false)}
        onPaid={() => {
          setPayOpen(false);
          refetch();
        }}
      />

      <PaymentModal
        isOpen={balancePayOpen}
        reservationId={balancePayReservationId}
        balanceInfo={balanceInfo}
        onClose={() => {
          setBalancePayOpen(false);
          setBalancePayReservationId(null);
          setBalanceInfo(null);
          setPendingAction(null);
        }}
        onPaid={async () => {
          setBalancePayOpen(false);
          setBalancePayReservationId(null);
          setBalanceInfo(null);

          // Después del pago exitoso, ejecutar la acción pendiente automáticamente
          if (balancePayReservationId && pendingAction) {
            try {
              const action =
                pendingAction === "check_in" ? "check_in" : "check_out";
              await fetchWithAuth(
                `${getApiURL()}/api/reservations/${balancePayReservationId}/${action}/`,
                {
                  method: "POST",
                }
              );

              // Mostrar mensaje de éxito después de la acción automática
              const actionText =
                pendingAction === "check_in" ? "Check-in" : "Check-out";
              showSuccessMessage(
                `${actionText} Exitoso`,
                `El pago ha sido procesado y la reserva #${balancePayReservationId} ha sido registrada como ${actionText.toLowerCase()} exitosamente.`
              );
            } catch (error) {
              console.error(`Error en ${pendingAction} automático:`, error);
            }
          }

          setPendingAction(null);
          refetch();
        }}
      />

      <CancellationModal
        isOpen={cancelModalOpen}
        onClose={() => {
          setCancelModalOpen(false);
          setCancelReservation(null);
        }}
        reservation={cancelReservation}
        onSuccess={() => {
          setCancelModalOpen(false);
          setCancelReservation(null);
          refetch();
          // Refrescar datos de habitaciones en el modal multi-habitación si está abierto
          setMultiRoomRefreshKey((prev) => prev + 1);
        }}
      />

      <Filter>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">
              {t("common.search")}
            </label>
            <input
              className="border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm w-64 transition-all"
              placeholder={t(
                "dashboard.reservations_management.search_placeholder"
              )}
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            />
          </div>

          <Formik
            enableReinitialize
            initialValues={{ hotel: filters.hotel, room: filters.room }}
            onSubmit={() => {}}
          >
            {() => (
              <>
                <div className="w-56">
                  <SelectAsync
                    title={t("dashboard.reservations_management.hotel")}
                    name="hotel"
                    resource="hotels"
                    placeholder={t("dashboard.reservations_management.all")}
                    getOptionLabel={(h) => h?.name}
                    getOptionValue={(h) => h?.id}
                    onValueChange={(opt, val) =>
                      setFilters((f) => ({ ...f, hotel: String(val || "") }))
                    }
                    extraParams={
                      !isSuperuser && hotelIdsString
                        ? { ids: hotelIdsString }
                        : {}
                    }
                  />
                </div>

                <div className="w-56">
                  <SelectAsync
                    title={t("dashboard.reservations_management.room")}
                    name="room"
                    resource="rooms"
                    placeholder={t(
                      "dashboard.reservations_management.all_rooms"
                    )}
                    getOptionLabel={(r) => r?.name || r?.number || `#${r?.id}`}
                    getOptionValue={(r) => r?.id}
                    extraParams={{ hotel: filters.hotel || undefined }}
                    onValueChange={(opt, val) =>
                      setFilters((f) => ({ ...f, room: String(val || "") }))
                    }
                  />
                </div>
              </>
            )}
          </Formik>

          <div className="w-56">
            <label className="text-xs text-aloja-gray-800/60">
              {t("dashboard.reservations_management.status")}
            </label>
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
              value={filters.status}
              onChange={(e) =>
                setFilters((f) => ({ ...f, status: e.target.value }))
              }
            >
              <option value="">
                {t("dashboard.reservations_management.all")}
              </option>
              {RES_STATUS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">
              {t("dashboard.reservations_management.from")}
            </label>
            <input
              type="date"
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateFrom}
              onChange={(e) =>
                setFilters((f) => ({ ...f, dateFrom: e.target.value }))
              }
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs text-aloja-gray-800/60">
              {t("dashboard.reservations_management.to")}
            </label>
            <input
              type="date"
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={filters.dateTo}
              onChange={(e) =>
                setFilters((f) => ({ ...f, dateTo: e.target.value }))
              }
            />
          </div>

          <div className="ml-auto">
            <button
              className="px-3 py-2 rounded-md border text-sm"
              onClick={() =>
                setFilters({
                  search: "",
                  hotel: "",
                  room: "",
                  status: "",
                  dateFrom: "",
                  dateTo: "",
                })
              }
            >
              {t("dashboard.reservations_management.clear_filters")}
            </button>
          </div>
        </div>
      </Filter>

      {!canViewReservation ? (
        <div className="text-center py-8 text-gray-500">
          {t("dashboard.reservations_management.no_permission_view", "No tienes permiso para ver reservas")}
        </div>
      ) : (
        <TableGeneric
          isLoading={isPending}
          data={displayResults}
          getRowId={(r) => r.id}
          defaultSort={{ key: "id", direction: "desc" }}
          columns={[
          {
            key: "display_name",
            header: t(
              "dashboard.reservations_management.table_headers.reservation"
            ),
            sortable: true,
            render: (r) => {
              if (r.is_group && r.group_code) {
                const roomsCount =
                  r.rooms_count || (r.group_reservations?.length ?? 0) || 1;
                return (
                  <div className="flex flex-col">
                    <button 
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMultiRoomGroup({
                          groupCode: r.group_code,
                          groupReservations: r.group_reservations || [],
                        });
                        setShowMultiRoomDetail(true);
                      }}
                      className="text-left text-blue-600 hover:text-blue-800 hover:underline"
                      title="Click para ver detalle de todas las habitaciones"
                    >
                      {r.display_name}
                    </button>
                    <span className="text-[11px] text-blue-700 font-semibold">
                      Multi-habitación · {roomsCount} hab.
                    </span>
                  </div>
                );
              }
              return r.display_name;
            },
          },
          {
            key: "guest_name",
            header: t("dashboard.reservations_management.table_headers.guest"),
            sortable: true,
            render: (r) => (
              <button
                type="button"
                className="text-blue-600 hover:text-blue-800 cursor-pointer text-left"
                onClick={(e) => {
                  e.stopPropagation();
                  setGuestDetailsReservation(r);
                  setGuestDetailsOpen(true);
                }}
                title="Ver datos del huésped"
              >
                {r.guest_name || "—"}
              </button>
            ),
          },
          {
            key: "hotel_name",
            header: t("dashboard.reservations_management.table_headers.hotel"),
            sortable: true,
          },
          {
            key: "room_name",
            header: t("dashboard.reservations_management.table_headers.room"),
            sortable: true,
            render: (r) => {
              if (r.is_group && r.group_code) {
                const roomsCount =
                  r.rooms_count || (r.group_reservations?.length ?? 0) || 1;
                return (
                  <span>
                    {roomsCount === 1
                      ? r.room_name || ""
                      : `${roomsCount} habitaciones`}
                  </span>
                );
              }
              return r.room_name;
            },
          },
          {
            key: "channel",
            header: t(
              "dashboard.reservations_management.table_headers.channel"
            ),
            sortable: true,
            render: (r) => {
              const isOta = r.is_ota || r.external_id;
              const channel = r.channel_display || r.channel || "Directo";
              const channelValue = r.channel || "direct";

              // Colores según el canal
              const getChannelBadge = () => {
                if (!isOta) {
                  // Reservas directas (sin OTA)
                  if (channelValue === "whatsapp") {
                    return (
                      <Badge variant="warning" size="sm" icon={WhatsappIcon}>
                        WhatsApp
                      </Badge>
                    );
                  }
                  return (
                    <Badge variant="directo" size="sm">
                      Directo
                    </Badge>
                  );
                }

                // Badge según el tipo de canal OTA
                // Detectar Google Calendar por notes o external_id
                const isGoogle =
                  (r.notes || "").toLowerCase().includes("google calendar") ||
                  (r.external_id || "").includes("@google.com");

                switch (channelValue) {
                  case "booking":
                    return (
                      <Badge variant="booking" size="sm">
                        Booking
                      </Badge>
                    );
                  case "airbnb":
                    return (
                      <Badge variant="airbnb" size="sm">
                        Airbnb
                      </Badge>
                    );
                  case "expedia":
                    return (
                      <Badge variant="airbnb" size="sm">
                        Expedia
                      </Badge>
                    );
                  case "other":
                    if (isGoogle) {
                      return (
                        <Badge variant="google" size="sm">
                          Google Calendar
                        </Badge>
                      );
                    }
                    return (
                      <Badge variant="warning" size="sm">
                        {channel}
                      </Badge>
                    );
                  default:
                    return (
                      <Badge variant="warning" size="sm">
                        {channel}
                      </Badge>
                    );
                }
              };

              return (
                <div className="flex items-center gap-1">
                  {getChannelBadge()}
                </div>
              );
            },
          },
          {
            key: "check_in",
            header: t(
              "dashboard.reservations_management.table_headers.check_in"
            ),
            sortable: true,
            accessor: (e) =>
              e.check_in ? format(parseISO(e.check_in), "dd/MM/yyyy") : "",
            render: (e) =>
              e.check_in ? format(parseISO(e.check_in), "dd/MM/yyyy") : "",
          },
          {
            key: "check_out",
            header: t(
              "dashboard.reservations_management.table_headers.check_out"
            ),
            sortable: true,
            accessor: (e) =>
              e.check_out ? format(parseISO(e.check_out), "dd/MM/yyyy") : "",
            render: (e) =>
              e.check_out ? format(parseISO(e.check_out), "dd/MM/yyyy") : "",
          },
          {
            key: "created_at",
            header: t(
              "dashboard.reservations_management.table_headers.created"
            ),
            sortable: true,
            accessor: (e) =>
              e.created_at
                ? format(parseISO(e.created_at), "dd/MM/yyyy HH:mm")
                : "",
            render: (e) =>
              e.created_at
                ? format(parseISO(e.created_at), "dd/MM/yyyy HH:mm")
                : "",
          },
          {
            key: "guests",
            header: t(
              "dashboard.reservations_management.table_headers.guests_count"
            ),
            sortable: true,
            right: true,
          },
          {
            key: "total_price",
            header: t("dashboard.reservations_management.table_headers.total"),
            sortable: true,
            right: true,
            render: (r) => {
              const fallback = `$ ${convertToDecimal(r.total_price)}`
              const getCurrencyCode = () => {
                if (r?.is_group && Array.isArray(r.group_reservations) && r.group_reservations.length > 0) {
                  const codes = new Set(
                    r.group_reservations
                      .map((rr) => rr?.pricing_currency_code)
                      .filter(Boolean)
                      .map((c) => String(c).toUpperCase())
                  )
                  if (codes.size === 1) return Array.from(codes)[0]
                  if (codes.size > 1) return "MIX"
                  return null
                }
                return (r?.pricing_currency_code ? String(r.pricing_currency_code).toUpperCase() : null)
              }

              const code = getCurrencyCode()
              if (!code) return fallback

              let formatted = fallback
              try {
                const amount = parseFloat(r.total_price || 0) || 0
                // Queremos símbolo "$" siempre adelante (sin "US$"), y el código al final.
                // Por eso NO usamos style:"currency" (que en es-AR muestra US$ para USD).
                const number = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount)
                formatted = `$ ${number}`
              } catch {
                formatted = fallback
              }

              // Mostrar el código al final, en la misma línea (ej: "$ 363.000,00 ARS")
              if (code === "MIX") return `${formatted} MIX`
              return `${formatted} ${code}`
            },
          },
          {
            key: "payment_status",
            header: "Estado de Pagos",
            sortable: false,
            render: (r) => (
              <div className="flex items-center gap-1 flex-wrap">
                <Tooltip
                  content={
                    <PaymentTooltip reservationId={r.id} reservationData={r} />
                  }
                  position="bottom"
                  maxWidth="320px"
                >
                  <PaymentStatusBadge
                    reservationId={r.id}
                    reservationData={r}
                  />
                </Tooltip>
                {r.paid_by === "ota" &&
                  (() => {
                    let channelName = r.channel_display || r.channel || "OTA";
                    if (!r.channel_display && r.channel) {
                      channelName =
                        r.channel.charAt(0).toUpperCase() + r.channel.slice(1);
                    }
                    return (
                      <Badge variant="success" size="sm">
                        Pagada por {channelName}
                      </Badge>
                    );
                  })()}
                {r.paid_by === "hotel" && (
                  <Badge variant="info" size="sm">
                    Pago directo
                  </Badge>
                )}
              </div>
            ),
          },
          {
            key: "status",
            header: t("dashboard.reservations_management.table_headers.status"),
            sortable: true,
            render: (r) => (
              <div className="flex items-center gap-1 flex-wrap">
                <Badge variant={`reservation-${r.status}`} size="sm">
                  {getStatusLabel(r.status, t)}
                </Badge>
                {r.overbooking_flag && (
                  <Badge variant="warning" size="sm">
                    Overbooking
                  </Badge>
                )}
              </div>
            ),
          },
          {
            key: "invoice_status",
            header: "Estado Facturación",
            sortable: false,
            render: (r) => <InvoiceStatus reservationId={r.id} />,
          },
          {
            key: "actions",
            header: t(
              "dashboard.reservations_management.table_headers.actions"
            ),
            sortable: false,
            right: true,
            render: (r) => (
              <div className="flex justify-end items-center gap-1">
                {/* Botón Editar */}
                {canEdit(r) && (
                  <button
                    onClick={() => onEdit(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100 transition-colors flex items-center gap-1"
                    title={t("dashboard.reservations_management.tooltips.edit")}
                  >
                    <EditIcon size="14" />
                    {t("dashboard.reservations_management.actions.edit")}
                  </button>
                )}
                {/* Botón Confirmar */}
                {canConfirm(r) && (
                  <button
                    onClick={() => onConfirm(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-green-50 text-green-700 border-green-300 hover:bg-green-100 transition-colors flex items-center gap-1"
                    title={t(
                      "dashboard.reservations_management.tooltips.confirm"
                    )}
                  >
                    <CheckIcon size="14" />
                    {t("dashboard.reservations_management.actions.confirm")}
                  </button>
                )}
                {/* Botón Check-in */}
                {canCheckIn(r) && (
                  <button
                    onClick={() => onCheckIn(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-yellow-50 text-yellow-700 border-yellow-300 hover:bg-yellow-100 transition-colors flex items-center gap-1"
                    title={t(
                      "dashboard.reservations_management.tooltips.check_in"
                    )}
                  >
                    <CheckinIcon size="14" />
                    {t("dashboard.reservations_management.actions.check_in")}
                  </button>
                )}
                {/* Botón Check-out */}
                {canCheckOut(r) && (
                  <button
                    onClick={() => onCheckOut(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-blue-50 text-blue-700 border-blue-300 hover:bg-blue-100 transition-colors flex items-center gap-1"
                    title={t(
                      "dashboard.reservations_management.tooltips.check_out"
                    )}
                  >
                    <CheckoutIcon size="14" />
                    {t("dashboard.reservations_management.actions.check_out")}
                  </button>
                )}
                {/* Botón Early Check-out */}
                {canEarlyCheckOut(r) && (
                  <button
                    onClick={() => onEarlyCheckOut(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-orange-50 text-orange-700 border-orange-300 hover:bg-orange-100 transition-colors flex items-center gap-1"
                    title={t(
                      "dashboard.reservations_management.tooltips.early_check_out"
                    )}
                  >
                    <EarlyCheckoutIcon size="14" />
                    {t(
                      "dashboard.reservations_management.actions.early_check_out"
                    )}
                  </button>
                )}

                {/* Botón Generar Factura/Comprobante */}
                {canGenerateInvoice(r) &&
                  (() => {
                    const docType = getDocumentType(r);
                    if (docType === "invoice") {
                      return (
                        <button
                          onClick={() => onGenerateInvoice(r)}
                          disabled={acting}
                          className="px-2 py-1 rounded text-xs border bg-green-50 text-green-700 border-green-300 hover:bg-green-100 transition-colors flex items-center gap-1"
                          title="Generar Factura Electrónica"
                        >
                          <InvoiceIcon size="14" />
                          Factura
                        </button>
                      );
                    } else if (docType === "receipt") {
                      return (
                        <button
                          onClick={() => onGenerateReceipt(r)}
                          disabled={acting}
                          className="px-2 py-1 rounded text-xs border bg-violet-50 text-violet-700 border-violet-300 hover:bg-violet-100 transition-colors flex items-center gap-1"
                          title="Generar Comprobante de Pago"
                        >
                          <InvoiceIcon size="14" />
                          Comprobante
                        </button>
                      );
                    }
                    return null;
                  })()}

                {/* Botón Cancelar */}
                {canCancel(r) && (
                  <button
                    onClick={() => onCancel(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-red-50 text-red-700 border-red-300 hover:bg-red-100 transition-colors flex items-center gap-1"
                    title={getCancelTooltip(r)}
                  >
                    <CancelIcon size="14" />
                    {getCancelMessage(r)}
                  </button>
                )}
                {/* Botón Imprimir Ficha del Pasajero */}
                {r.status === "check_in" && (
                  <button
                    onClick={() => handlePrintGuestCard(r)}
                    disabled={acting}
                    className="px-2 py-1 rounded text-xs border bg-purple-50 text-purple-700 border-purple-300 hover:bg-purple-100 transition-colors flex items-center gap-1"
                    title="Imprimir ficha del pasajero"
                  >
                    <PrintIcon size="14" />
                    Ficha
                  </button>
                )}
              </div>
            ),
          },
        ]}
        />
      )}

      {canViewReservation && hasNextPage && displayResults?.length >= 50 && (
        <div>
          <button
            className="px-3 py-2 rounded-md border"
            onClick={() => fetchNextPage()}
          >
            {t("dashboard.reservations_management.load_more")}
          </button>
        </div>
      )}

      {/* Modal de confirmación para Early Check-out */}
      <AlertSwal
        isOpen={showEarlyCheckOutAlert}
        onClose={() => {
          setShowEarlyCheckOutAlert(false);
          setEarlyCheckOutReservation(null);
        }}
        onConfirm={handleEarlyCheckOutConfirm}
        confirmLoading={false}
        title={t(
          "dashboard.reservations_management.confirmations.early_check_out_title"
        )}
        description={
          earlyCheckOutReservation
            ? t(
                "dashboard.reservations_management.confirmations.early_check_out",
                {
                  guest: earlyCheckOutReservation.guest_name,
                  room: earlyCheckOutReservation.room_name,
                }
              )
            : ""
        }
        confirmText={t("common.yes")}
        cancelText={t("common.cancel")}
        tone="warning"
      />

      {/* Modal de mensaje de éxito */}
      <AlertSwal
        isOpen={showSuccessAlert}
        onClose={() => {
          setShowSuccessAlert(false);
          setSuccessData(null);
        }}
        onConfirm={() => {
          setShowSuccessAlert(false);
          setSuccessData(null);
        }}
        confirmLoading={false}
        title={successData?.title || ""}
        description={successData?.description || ""}
        confirmText="Aceptar"
        cancelText=""
        tone="success"
      />

      {/* Modal de mensaje de información */}
      <AlertSwal
        isOpen={showInfoAlert}
        onClose={() => {
          setShowInfoAlert(false);
          setInfoData(null);
        }}
        onConfirm={() => {
          if (infoData?.onConfirm) {
            infoData.onConfirm();
          }
          setShowInfoAlert(false);
          setInfoData(null);
        }}
        confirmLoading={false}
        title={infoData?.title || ""}
        description={infoData?.description || ""}
        confirmText={infoData?.onConfirm ? "Ver" : "Aceptar"}
        cancelText=""
        tone={infoData?.tone || "info"}
      />

      {/* Mini-modal: Selección Condición IVA para Factura */}
      {showInvoiceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-4">
            <div className="mb-3">
              <h3 className="text-lg font-semibold text-aloja-navy">
                Datos fiscales del receptor
              </h3>
              <p className="text-xs text-aloja-gray-800/70 mt-1">
                Seleccioná la condición frente al IVA del huésped. Para
                Consumidor Final no es necesario documento.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-aloja-gray-800/60">
                  Condición frente al IVA
                </label>
                <select
                  className="mt-1 border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                  value={selectedTaxCondition}
                  onChange={(e) => setSelectedTaxCondition(e.target.value)}
                >
                  <option value="5">Consumidor Final</option>
                  <option value="1">Responsable Inscripto</option>
                  <option value="8">Monotributista</option>
                  <option value="6">Exento</option>
                </select>
              </div>

              {selectedTaxCondition !== "5" && (
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-1">
                    <label className="text-xs text-aloja-gray-800/60">
                      Tipo Doc.
                    </label>
                    <select
                      className="mt-1 border border-gray-200 rounded-lg px-2 py-2 text-sm w-full"
                      value={selectedDocType}
                      onChange={(e) => setSelectedDocType(e.target.value)}
                    >
                      <option value="80">CUIT</option>
                      <option value="96">DNI</option>
                      <option value="99">Consumidor Final</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs text-aloja-gray-800/60">
                      Nº Documento
                    </label>
                    <input
                      className="mt-1 border border-gray-200 rounded-lg px-3 py-2 text-sm w-full"
                      placeholder={
                        selectedDocType === "80"
                          ? "CUIT (11 dígitos)"
                          : "Documento"
                      }
                      value={selectedDocNumber}
                      onChange={(e) => setSelectedDocNumber(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button
                className="px-3 py-2 rounded-md border text-sm"
                onClick={() => {
                  setShowInvoiceModal(false);
                  setInvoiceReservation(null);
                }}
                disabled={isCreatingInvoice}
              >
                Cancelar
              </button>
              <button
                className="px-3 py-2 rounded-md border bg-green-600 text-white text-sm disabled:opacity-60"
                disabled={
                  isCreatingInvoice ||
                  !invoiceReservation ||
                  (selectedTaxCondition !== "5" && !selectedDocNumber)
                }
                onClick={async () => {
                  if (!invoiceReservation) return;
                  try {
                    setIsCreatingInvoice(true);
                    const isCF = selectedTaxCondition === "5";
                    const body = {
                      reservation_id: invoiceReservation.id,
                      invoice_type: "B",
                      client_name: invoiceReservation.guest_name || "Cliente",
                      client_tax_condition: selectedTaxCondition,
                      client_document_type: isCF
                        ? "99"
                        : selectedDocType || "80",
                      client_document_number: isCF
                        ? "0"
                        : selectedDocNumber || "0",
                      issue_date: new Date().toISOString().split("T")[0],
                    };
                    const response = await fetchWithAuth(
                      `${getApiURL()}/api/invoicing/invoices/create-from-reservation/`,
                      {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                      }
                    );
                    if (response) {
                      showInfoMessage(
                        "Factura Generada",
                        `La factura ${response.number} ha sido creada exitosamente`,
                        "success"
                      );
                      refetch();
                    }
                    setShowInvoiceModal(false);
                    setInvoiceReservation(null);
                  } catch (error) {
                    console.error("Error generando factura:", error);
                    showInfoMessage(
                      "Error",
                      `Error generando factura: ${
                        error?.message || "Error desconocido"
                      }`,
                      "danger"
                    );
                  } finally {
                    setIsCreatingInvoice(false);
                  }
                }}
              >
                {isCreatingInvoice ? "Generando…" : "Generar factura"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
