import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import Badge from "src/components/Badge";
import Button from "src/components/Button";
import SpinnerLoading from "src/components/SpinnerLoading";
import { useHasAnyPermission } from "src/hooks/usePermissions";
import { cashboxService } from "src/services/cashboxService";

const Cashbox = () => {
  const { t } = useTranslation();
  const canViewCashbox = useHasAnyPermission([
    "cashbox.view_cashsession",
    "cashbox.view_cashbox_reports",
    "cashbox.open_cashsession",
    "cashbox.close_cashsession",
  ]);

  const [hotelId, setHotelId] = useState(null);
  const [activeTab, setActiveTab] = useState("general");
  const [pageLoading, setPageLoading] = useState(true);
  const [pending, setPending] = useState({
    refresh: false,
    open: false,
    close: false,
    movement: false,
  });
  const [session, setSession] = useState(null);
  const [movements, setMovements] = useState([]);
  const [error, setError] = useState("");

  const [openingAmount, setOpeningAmount] = useState("0.00");
  const [closingAmount, setClosingAmount] = useState("");
  const [movementAmount, setMovementAmount] = useState("");
  const [movementDescription, setMovementDescription] = useState("");
  const [movementType, setMovementType] = useState("in");

  const currency = useMemo(() => "ARS", []);

  const [historicalLoading, setHistoricalLoading] = useState(false);
  const [historicalSessions, setHistoricalSessions] = useState([]);
  const [historicalError, setHistoricalError] = useState("");
  const [historicalFilters, setHistoricalFilters] = useState({ from: "", to: "", status: "" });
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedMovements, setSelectedMovements] = useState([]);
  const [selectedLoading, setSelectedLoading] = useState(false);
  const [selectedError, setSelectedError] = useState("");

  const fmt = useMemo(() => {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }, [currency]);

  const toNumber = (v) => {
    if (v === null || v === undefined) return null;
    if (typeof v === "number") return Number.isFinite(v) ? v : null;
    const s = String(v).replace(",", ".").trim();
    if (!s) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  };

  const money = (v) => {
    const n = toNumber(v);
    return n === null ? "-" : fmt.format(n);
  };

  const statusBadge = (st) => {
    if (st === "open") return { variant: "success", label: "Abierta" };
    if (st === "closed") return { variant: "default", label: "Cerrada" };
    if (st === "cancelled") return { variant: "error", label: "Anulada" };
    return { variant: "info", label: st || "-" };
  };

  const loadMovements = async ({ hid, sessionId }) => {
    if (!hid || !sessionId) {
      setMovements([]);
      return;
    }
    try {
      const data = await cashboxService.listMovements({ hotelId: hid, sessionId });
      const items = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
      setMovements(items);
    } catch {
      setMovements([]);
    }
  };

  const loadCurrent = async (hid, { silent = false } = {}) => {
    try {
      if (!silent) setError("");
      const data = await cashboxService.getCurrentSession({ hotelId: hid, currency });
      setSession(data);
      await loadMovements({ hid, sessionId: data?.id });
    } catch (e) {
      const msg = String(e?.message || "");
      if (msg.includes("HTTP 404")) {
        setSession(null);
        setMovements([]);
      } else {
        setError(msg || t("common.error", "Error"));
      }
    } finally {
      if (!silent) setPageLoading(false);
    }
  };

  const loadHistoricalSessions = async ({ hid, filters }) => {
    if (!hid) return;
    try {
      setHistoricalError("");
      setHistoricalLoading(true);
      const data = await cashboxService.listSessions({
        hotelId: hid,
        status: filters?.status || undefined,
      });
      const items = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
      const from = filters?.from ? new Date(`${filters.from}T00:00:00`) : null;
      const to = filters?.to ? new Date(`${filters.to}T23:59:59`) : null;
      const filtered = items.filter((s) => {
        const d = s?.opened_at ? new Date(s.opened_at) : null;
        if (!d || Number.isNaN(d.getTime())) return true;
        if (from && d < from) return false;
        if (to && d > to) return false;
        return true;
      });
      setHistoricalSessions(filtered);
    } catch (e) {
      setHistoricalError(String(e?.message || "Error cargando histórico"));
      setHistoricalSessions([]);
    } finally {
      setHistoricalLoading(false);
    }
  };

  const loadSelectedSession = async ({ hid, sessionId }) => {
    if (!hid || !sessionId) return;
    try {
      setSelectedError("");
      setSelectedLoading(true);
      const data = await cashboxService.getSession({ sessionId });
      setSelectedSession(data);
      const mov = await cashboxService.listMovements({ hotelId: hid, sessionId });
      const items = Array.isArray(mov) ? mov : Array.isArray(mov?.results) ? mov.results : [];
      setSelectedMovements(items);
    } catch (e) {
      setSelectedError(String(e?.message || "Error cargando detalle"));
      setSelectedSession(null);
      setSelectedMovements([]);
    } finally {
      setSelectedLoading(false);
    }
  };

  useEffect(() => {
    const userHotelId = localStorage.getItem("hotelId") || "1";
    setHotelId(userHotelId);
    loadCurrent(userHotelId);
  }, []);

  useEffect(() => {
    if (activeTab !== "historical" || !hotelId) return;
    loadHistoricalSessions({ hid: hotelId, filters: historicalFilters });
  }, [activeTab, hotelId]);

  const handleOpen = async () => {
    try {
      setError("");
      setPending((p) => ({ ...p, open: true }));
      const data = await cashboxService.openSession({
        hotelId,
        openingAmount: openingAmount === "" ? 0 : openingAmount,
        currency,
      });
      setSession(data);
      setClosingAmount("");
      await loadMovements({ hid: hotelId, sessionId: data?.id });
    } catch (e) {
      setError(String(e?.message || "Error abriendo caja"));
    } finally {
      setPending((p) => ({ ...p, open: false }));
    }
  };

  const handleClose = async () => {
    try {
      setError("");
      setPending((p) => ({ ...p, close: true }));
      const data = await cashboxService.closeSession({
        sessionId: session.id,
        closingAmount,
      });
      setSession(data);
    } catch (e) {
      setError(String(e?.message || "Error cerrando caja"));
    } finally {
      setPending((p) => ({ ...p, close: false }));
    }
  };

  const handleMovement = async () => {
    try {
      setError("");
      setPending((p) => ({ ...p, movement: true }));
      await cashboxService.createMovement({
        sessionId: session.id,
        hotelId,
        movementType,
        amount: movementAmount,
        currency,
        description: movementDescription,
      });
      setMovementAmount("");
      setMovementDescription("");
      await loadCurrent(hotelId, { silent: true });
    } catch (e) {
      setError(String(e?.message || "Error creando movimiento"));
    } finally {
      setPending((p) => ({ ...p, movement: false }));
    }
  };

  const handleRefresh = async () => {
    try {
      setPending((p) => ({ ...p, refresh: true }));
      await loadCurrent(hotelId, { silent: true });
      if (activeTab === "historical") {
        await loadHistoricalSessions({ hid: hotelId, filters: historicalFilters });
        if (selectedSessionId) await loadSelectedSession({ hid: hotelId, sessionId: selectedSessionId });
      }
    } finally {
      setPending((p) => ({ ...p, refresh: false }));
    }
  };

  if (!canViewCashbox) {
    return (
      <div className="p-6 text-center text-gray-600">
        {t("cashbox.no_permission", "No tenés permiso para ver la caja.")}
      </div>
    );
  }

  if (pageLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <SpinnerLoading />
      </div>
    );
  }

  const expectedCurrent = toNumber(session?.expected_amount_current) ?? 0;
  const closingN = toNumber(closingAmount);
  const diffPreview = closingN === null ? null : closingN - expectedCurrent;
  const movementN = toNumber(movementAmount);
  const canAddMovement =
    !!session && session.status === "open" && movementN !== null && movementN > 0 && !pending.movement;
  const canClose = !!session && session.status === "open" && closingN !== null && !pending.close;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="space-y-1">
          <div className="text-xs text-aloja-gray-800/60">{t("sidebar.financial")}</div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold text-aloja-navy">{t("sidebar.cashbox", "Caja")}</h1>
            {session?.status ? (
              <Badge variant={statusBadge(session.status).variant} size="md">
                {statusBadge(session.status).label}
              </Badge>
            ) : (
              <Badge variant="warning" size="md">Sin abrir</Badge>
            )}
          </div>
          <div className="text-sm text-gray-600">
            {session?.opened_at ? (
              <span>Última apertura: {new Date(session.opened_at).toLocaleString("es-AR")}</span>
            ) : (
              <span>Abrí la caja para comenzar a registrar el efectivo del turno.</span>
            )}
          </div>
        </div>
        <Button variant="outline" size="md" onClick={handleRefresh} isPending={pending.refresh} loadingText="Actualizando…">
          Actualizar
        </Button>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-sm flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="font-semibold">Ocurrió un error</div>
            <div className="text-red-700 break-words">{error}</div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setError("")}>Cerrar</Button>
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => setActiveTab("general")}
          className={`h-10 px-4 rounded-full border text-sm font-medium transition ${
            activeTab === "general"
              ? "bg-aloja-navy text-white border-aloja-navy shadow-sm"
              : "bg-white text-aloja-navy border-gray-200 hover:bg-gray-50"
          }`}
        >
          {t("cashbox.tabs.general", "General")}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("historical")}
          className={`h-10 px-4 rounded-full border text-sm font-medium transition ${
            activeTab === "historical"
              ? "bg-aloja-navy text-white border-aloja-navy shadow-sm"
              : "bg-white text-aloja-navy border-gray-200 hover:bg-gray-50"
          }`}
        >
          {t("cashbox.tabs.historical", "Histórico")}
        </button>
      </div>

      {activeTab === "historical" ? (
        <HistoricalTab
          t={t}
          money={money}
          toNumber={toNumber}
          statusBadge={statusBadge}
          hotelId={hotelId}
          currency={currency}
          loading={historicalLoading}
          sessions={historicalSessions}
          error={historicalError}
          filters={historicalFilters}
          setFilters={setHistoricalFilters}
          onApply={async () => loadHistoricalSessions({ hid: hotelId, filters: historicalFilters })}
          selectedSessionId={selectedSessionId}
          setSelectedSessionId={setSelectedSessionId}
          selectedSession={selectedSession}
          selectedMovements={selectedMovements}
          selectedLoading={selectedLoading}
          selectedError={selectedError}
          onSelect={async (id) => {
            setSelectedSessionId(id);
            await loadSelectedSession({ hid: hotelId, sessionId: id });
          }}
          onClearSelection={() => {
            setSelectedSessionId(null);
            setSelectedSession(null);
            setSelectedMovements([]);
            setSelectedError("");
          }}
        />
      ) : (
        <>
          {!session ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="space-y-1">
                    <div className="text-sm font-semibold text-aloja-navy">Apertura de caja</div>
                    <div className="text-sm text-gray-600">Definí el fondo inicial (cambio) para empezar el turno.</div>
                  </div>
                  <Badge variant="info" size="sm">ARS</Badge>
                </div>
                <div className="mt-4 flex items-end gap-3 flex-wrap">
                  <label className="text-sm">
                    <div className="text-xs text-gray-500">Fondo inicial</div>
                    <input
                      className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-52 focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                      value={openingAmount}
                      onChange={(e) => setOpeningAmount(e.target.value)}
                      placeholder="0.00"
                      inputMode="decimal"
                    />
                  </label>
                  <Button variant="primary" size="md" onClick={handleOpen} isPending={pending.open} loadingText="Abriendo…">
                    Abrir caja
                  </Button>
                </div>
              </div>
              <div className="p-5 bg-gradient-to-b from-aloja-navy to-aloja-navy2 rounded-xl text-white shadow-sm">
                <div className="text-sm font-semibold">¿Cómo funciona?</div>
                <ul className="mt-3 space-y-2 text-sm text-white/90">
                  <li><span className="font-semibold">1.</span> Abrís con un fondo inicial.</li>
                  <li><span className="font-semibold">2.</span> Se suman pagos en efectivo automáticamente.</li>
                  <li><span className="font-semibold">3.</span> Registrás ingresos/egresos manuales.</li>
                  <li><span className="font-semibold">4.</span> Cerrás con el efectivo contado y ves la diferencia.</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-3">
                <MetricCard label="Apertura" value={money(session.opening_amount)} hint="Fondo inicial" />
                <MetricCard label="Efectivo" value={money(session.cash_payments_total)} hint="Pagos en caja" />
                <MetricCard label="Ingresos" value={money(session.movements_in_total)} hint="Mov. manuales +" />
                <MetricCard label="Egresos" value={money(session.movements_out_total)} hint="Mov. manuales -" />
                <MetricCard label="Esperado" value={money(session.expected_amount_current)} hint="Saldo teórico" emphasis />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm space-y-4">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="text-sm font-semibold text-aloja-navy">Movimientos manuales</div>
                      <div className="text-xs text-gray-500">Ingresos/egresos que no vienen de una reserva.</div>
                    </div>
                    <Badge variant="info" size="sm">{currency}</Badge>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="sm:col-span-1">
                      <div className="text-xs text-gray-500">Tipo</div>
                      <div className="mt-1 grid grid-cols-2 gap-2">
                        <button
                          type="button"
                          onClick={() => setMovementType("in")}
                          className={`h-10 rounded-lg border text-xs font-medium transition ${
                            movementType === "in"
                              ? "border-green-300 bg-green-50 text-green-800"
                              : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                          }`}
                          disabled={session.status !== "open"}
                        >
                          Ingreso
                        </button>
                        <button
                          type="button"
                          onClick={() => setMovementType("out")}
                          className={`h-10 rounded-lg border text-xs font-medium transition ${
                            movementType === "out"
                              ? "border-red-300 bg-red-50 text-red-800"
                              : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                          }`}
                          disabled={session.status !== "open"}
                        >
                          Egreso
                        </button>
                      </div>
                    </div>
                    <label className="text-sm sm:col-span-1">
                      <div className="text-xs text-gray-500">Monto</div>
                      <input
                        className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                        value={movementAmount}
                        onChange={(e) => setMovementAmount(e.target.value)}
                        placeholder="0.00"
                        inputMode="decimal"
                        disabled={session.status !== "open"}
                      />
                      <div className="mt-1 text-xs text-gray-500">Solo positivos; el tipo define + / -</div>
                    </label>
                    <label className="text-sm sm:col-span-1">
                      <div className="text-xs text-gray-500">Detalle</div>
                      <input
                        className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                        value={movementDescription}
                        onChange={(e) => setMovementDescription(e.target.value)}
                        placeholder="Ej: compra insumos / retiro"
                        disabled={session.status !== "open"}
                      />
                      <div className="mt-1 text-xs text-gray-500">Opcional, pero recomendado.</div>
                    </label>
                  </div>
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="text-xs text-gray-500">
                      {session.status !== "open" ? "La caja está cerrada; no se pueden agregar movimientos." : " "}
                    </div>
                    <Button variant="neutral" size="md" onClick={handleMovement} disabled={!canAddMovement} isPending={pending.movement} loadingText="Agregando…">
                      Agregar movimiento
                    </Button>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="text-sm font-semibold text-aloja-navy">Recientes</div>
                    <div className="mt-2 space-y-2 max-h-52 overflow-auto pr-1">
                      {movements?.length ? (
                        movements.slice(0, 10).map((m) => {
                          const isIn = m.movement_type === "in";
                          const sign = isIn ? "+" : "-";
                          return (
                            <div key={m.id} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-gray-50 border border-gray-100">
                              <div className="min-w-0">
                                <div className="text-sm text-gray-800 truncate">
                                  {m.description || (isIn ? "Ingreso manual" : "Egreso manual")}
                                </div>
                                <div className="text-xs text-gray-500">
                                  {m.created_at ? new Date(m.created_at).toLocaleString("es-AR") : ""}
                                </div>
                              </div>
                              <div className={`text-sm font-semibold ${isIn ? "text-green-700" : "text-red-700"}`}>
                                {sign} {money(m.amount)}
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <div className="text-sm text-gray-500">Todavía no hay movimientos.</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-2 p-5 bg-white rounded-xl border border-gray-200 shadow-sm space-y-4">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <div className="text-sm font-semibold text-aloja-navy">Cierre de caja</div>
                      <div className="text-xs text-gray-500">Ingresá el efectivo contado. El sistema calcula la diferencia automáticamente.</div>
                    </div>
                    <Badge variant={statusBadge(session.status).variant} size="sm">
                      {statusBadge(session.status).label}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
                      <div className="text-xs text-gray-500">Esperado</div>
                      <div className="mt-1 text-2xl font-semibold text-aloja-navy">{money(session.expected_amount_current)}</div>
                      <div className="mt-1 text-xs text-gray-500">Apertura + efectivo + ingresos − egresos</div>
                    </div>
                    <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
                      <div className="text-xs text-gray-500">Diferencia (preview)</div>
                      <div className={`mt-1 text-2xl font-semibold ${diffPreview === null ? "text-gray-400" : diffPreview === 0 ? "text-green-700" : diffPreview > 0 ? "text-green-700" : "text-red-700"}`}>
                        {diffPreview === null ? "-" : money(diffPreview)}
                      </div>
                      <div className="mt-1 text-xs text-gray-500">Contado − esperado</div>
                    </div>
                  </div>
                  {session.status === "open" ? (
                    <div className="flex items-end gap-3 flex-wrap">
                      <label className="text-sm">
                        <div className="text-xs text-gray-500">Efectivo contado</div>
                        <input
                          className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-56 focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                          value={closingAmount}
                          onChange={(e) => setClosingAmount(e.target.value)}
                          placeholder="0.00"
                          inputMode="decimal"
                        />
                      </label>
                      <Button variant="primary" size="md" onClick={handleClose} disabled={!canClose} isPending={pending.close} loadingText="Cerrando…">
                        Cerrar caja
                      </Button>
                      {diffPreview !== null && diffPreview !== 0 && (
                        <Badge variant="warning" size="sm">Atención: diferencia {money(diffPreview)}</Badge>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl border border-gray-200 bg-gray-50">
                      <div className="text-sm font-semibold text-aloja-navy">Caja cerrada</div>
                      <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        <div>
                          <div className="text-xs text-gray-500">Contado</div>
                          <div className="font-semibold">{money(session.closing_amount)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Esperado (snapshot)</div>
                          <div className="font-semibold">{money(session.expected_amount)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Diferencia</div>
                          <div className={`font-semibold ${toNumber(session.difference_amount) === 0 ? "text-green-700" : "text-red-700"}`}>
                            {money(session.difference_amount)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Cashbox;

function MetricCard({ label, value, hint, emphasis = false }) {
  return (
    <div className={`p-4 rounded-xl border shadow-sm ${emphasis ? "bg-aloja-navy text-white border-aloja-navy" : "bg-white border-gray-200"}`}>
      <div className={`text-xs ${emphasis ? "text-white/70" : "text-gray-500"}`}>{label}</div>
      <div className={`mt-1 text-xl font-semibold ${emphasis ? "text-white" : "text-aloja-navy"}`}>{value}</div>
      <div className={`mt-1 text-xs ${emphasis ? "text-white/70" : "text-gray-500"}`}>{hint}</div>
    </div>
  );
}

function HistoricalTab({
  t,
  money,
  toNumber,
  statusBadge,
  hotelId,
  currency,
  loading,
  sessions,
  error,
  filters,
  setFilters,
  onApply,
  selectedSessionId,
  selectedSession,
  selectedMovements,
  selectedLoading,
  selectedError,
  onSelect,
  onClearSelection,
}) {
  const statusToLabel = (st) => statusBadge(st)?.label || st || "-";
  const statusToVariant = (st) => statusBadge(st)?.variant || "default";

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div className="xl:col-span-2 space-y-3">
        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm space-y-4">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="text-sm font-semibold text-aloja-navy">Histórico de cajas</div>
              <div className="text-xs text-gray-500">Ver aperturas/cierres por sesión. Podés filtrar por fechas y estado.</div>
            </div>
            <Badge variant="info" size="sm">Hotel #{hotelId} · {currency}</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
            <label className="text-sm">
              <div className="text-xs text-gray-500">Desde</div>
              <input
                type="date"
                className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                value={filters.from}
                onChange={(e) => setFilters((s) => ({ ...s, from: e.target.value }))}
              />
            </label>
            <label className="text-sm">
              <div className="text-xs text-gray-500">Hasta</div>
              <input
                type="date"
                className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                value={filters.to}
                onChange={(e) => setFilters((s) => ({ ...s, to: e.target.value }))}
              />
            </label>
            <label className="text-sm">
              <div className="text-xs text-gray-500">Estado</div>
              <select
                className="mt-1 border border-gray-200 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-aloja-navy/20"
                value={filters.status}
                onChange={(e) => setFilters((s) => ({ ...s, status: e.target.value }))}
              >
                <option value="">Todos</option>
                <option value="open">Abierta</option>
                <option value="closed">Cerrada</option>
                <option value="cancelled">Anulada</option>
              </select>
            </label>
            <div className="flex gap-2">
              <Button variant="primary" size="md" onClick={onApply} isPending={loading} loadingText="Cargando…">
                Aplicar
              </Button>
              <Button variant="outline" size="md" onClick={() => setFilters({ from: "", to: "", status: "" })} disabled={loading}>
                Limpiar
              </Button>
            </div>
          </div>
          {error && <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-sm">{error}</div>}
        </div>

        <div className="p-0 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b bg-gray-50 flex items-center justify-between">
            <div className="text-sm font-semibold text-aloja-navy">Sesiones</div>
            <div className="text-xs text-gray-500">{sessions?.length || 0} resultados</div>
          </div>
          {loading ? (
            <div className="p-6">
              <SpinnerLoading inline size={36} label={t("common.loading", "Cargando…")} />
            </div>
          ) : sessions?.length ? (
            <div className="divide-y">
              {sessions.map((s) => {
                const isSelected = String(selectedSessionId) === String(s.id);
                const opened = s.opened_at ? new Date(s.opened_at).toLocaleString("es-AR") : "-";
                const closed = s.closed_at ? new Date(s.closed_at).toLocaleString("es-AR") : "—";
                const diff = toNumber(s.difference_amount);
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => onSelect(s.id)}
                    className={`w-full text-left px-5 py-4 transition ${isSelected ? "bg-aloja-navy/5" : "hover:bg-gray-50"}`}
                  >
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <div className="text-sm font-semibold text-aloja-navy">Caja #{s.id}</div>
                          <Badge variant={statusToVariant(s.status)} size="sm">{statusToLabel(s.status)}</Badge>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">Apertura: {opened} · Cierre: {closed}</div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Apertura</div>
                          <div className="text-sm font-semibold">{money(s.opening_amount)}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Contado</div>
                          <div className="text-sm font-semibold">{money(s.closing_amount)}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Diferencia</div>
                          <div className={`text-sm font-semibold ${diff === null ? "text-gray-500" : diff === 0 ? "text-green-700" : diff > 0 ? "text-green-700" : "text-red-700"}`}>
                            {money(s.difference_amount)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="p-6 text-sm text-gray-600">No hay cajas para los filtros seleccionados.</div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <div className="p-5 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <div className="text-sm font-semibold text-aloja-navy">Detalle</div>
              <div className="text-xs text-gray-500">Seleccioná una caja del listado.</div>
            </div>
            {selectedSessionId && (
              <Button variant="ghost" size="sm" onClick={onClearSelection}>Quitar selección</Button>
            )}
          </div>
          {!selectedSessionId ? (
            <div className="mt-4 text-sm text-gray-600">Elegí una sesión para ver el resumen calculado y sus movimientos.</div>
          ) : selectedLoading ? (
            <div className="mt-6">
              <SpinnerLoading inline size={36} label={t("common.loading", "Cargando…")} />
            </div>
          ) : selectedError ? (
            <div className="mt-4 p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-sm">{selectedError}</div>
          ) : !selectedSession ? (
            <div className="mt-4 text-sm text-gray-600">Sin datos.</div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="flex items-center gap-2 flex-wrap">
                <div className="text-lg font-semibold text-aloja-navy">Caja #{selectedSession.id}</div>
                <Badge variant={statusToVariant(selectedSession.status)} size="sm">{statusToLabel(selectedSession.status)}</Badge>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="text-xs text-gray-500">Esperado (calculado)</div>
                  <div className="mt-1 text-xl font-semibold text-aloja-navy">{money(selectedSession.expected_amount_current)}</div>
                  <div className="mt-1 text-xs text-gray-500">En base a pagos cash + movimientos.</div>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="text-xs text-gray-500">Diferencia (snapshot)</div>
                  <div className="mt-1 text-xl font-semibold">{money(selectedSession.difference_amount)}</div>
                  <div className="mt-1 text-xs text-gray-500">Al momento del cierre.</div>
                </div>
              </div>
              <div className="pt-2 border-t">
                <div className="text-sm font-semibold text-aloja-navy">Movimientos</div>
                <div className="mt-2 space-y-2 max-h-[420px] overflow-auto pr-1">
                  {selectedMovements?.length ? (
                    selectedMovements.map((m) => {
                      const isIn = m.movement_type === "in";
                      const sign = isIn ? "+" : "-";
                      return (
                        <div key={m.id} className="p-3 rounded-lg border border-gray-100 bg-gray-50 flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="text-sm text-gray-800 truncate">
                              {m.description || (isIn ? "Ingreso manual" : "Egreso manual")}
                            </div>
                            <div className="text-xs text-gray-500">
                              {m.created_at ? new Date(m.created_at).toLocaleString("es-AR") : ""}
                            </div>
                          </div>
                          <div className={`text-sm font-semibold ${isIn ? "text-green-700" : "text-red-700"}`}>
                            {sign} {money(m.amount)}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-sm text-gray-600">No hay movimientos en esta sesión.</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
