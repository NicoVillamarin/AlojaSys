import { useEffect, useMemo, useRef, useState } from "react";
import ModalLayout from "src/layouts/ModalLayout";
import { createPreference } from "src/services/payments";
import Swal from "sweetalert2";
import "animate.css";
import fetchWithAuth from "src/services/fetchWithAuth";
import { getApiURL } from "src/services/utils";
import PaymentBrick from "../payments/PaymentBrick";
import CrashIcon from "src/assets/icons/CrashIcon";
import TranfCrash from "src/assets/icons/TranfCrash";
import PostnetIcon from "src/assets/icons/PostnetIcon";
import CardCreditIcon from "src/assets/icons/CardCreditIcon";
import { paymentPolicyService } from "src/services/paymentPolicyService";
import SpinnerLoading from "src/components/SpinnerLoading";

export default function PaymentModal({
  isOpen,
  reservationId,
  amount,             // opcional: para seña/depósito
  balanceInfo,        // opcional: información del saldo pendiente { balance_due, total_paid, total_reservation, payment_required_at }
  onClose,
  onPaid,            // callback cuando detectamos status=confirmed
}) {
  const [loading, setLoading] = useState(false);
  const [pref, setPref] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
    const [payStatus, setPayStatus] = useState("");
    const [payDetail, setPayDetail] = useState("");
    // sin brick embebido: usaremos link directo a init_point
    const attemptsRef = useRef(0);
    // Campos de formulario simple (Checkout API)
    const [ccNumber, setCcNumber] = useState("");
    const [ccMonth, setCcMonth] = useState("11");
    const [ccYear, setCcYear] = useState("2030");
    const [ccCvv, setCcCvv] = useState("123");
    const [ccName, setCcName] = useState("APRO");
    const [docType, setDocType] = useState("DNI");
    const [docNumber, setDocNumber] = useState("12345678");
    const [email, setEmail] = useState("");
    const [installments, setInstallments] = useState(1);
    const [paymentMethod, setPaymentMethod] = useState(""); // card, cash, transfer, pos
    // Steps: amount -> select -> form
    const [step, setStep] = useState("amount");
    
    // Determinar si es pago de saldo pendiente o confirmación inicial
    const isBalancePayment = !!balanceInfo;

    // Reserva y política
    const [reservationData, setReservationData] = useState(null); // { hotel: id, total_price }
    const [policy, setPolicy] = useState(null);
    const [depositInfo, setDepositInfo] = useState(null); // { required, amount, type, ... }
    const [payAmount, setPayAmount] = useState(null); // número para preferencia (seña) o null para total

    // Función para registrar pago manual (efectivo, transferencia, POS)
    const registerManualPayment = async (paymentType, additionalData = {}) => {
        try {
            setError("");
            
            // Determinar el monto correcto del pago
            let paymentAmount;
            if (isBalancePayment) {
                // Pago de saldo pendiente
                paymentAmount = balanceInfo.balance_due;
            } else if (payAmount !== null) {
                // Pago de seña (monto específico)
                paymentAmount = payAmount;
            } else {
                // Pago total (payAmount es null)
                paymentAmount = reservationData?.total_price || 0;
            }
            
            const response = await fetchWithAuth(`${getApiURL()}/api/reservations/${reservationId}/payments/`, {
                method: "POST",
                body: JSON.stringify({
                    amount: paymentAmount,
                    method: paymentType,
                    date: new Date().toISOString().split('T')[0] // Fecha actual en formato YYYY-MM-DD
                })
            });

            if (response?.id) {
                // Solo actualizar el estado de la reserva a confirmada si es confirmación inicial
                if (!isBalancePayment) {
                    await fetchWithAuth(`${getApiURL()}/api/reservations/${reservationId}/`, {
                        method: "PATCH",
                        body: JSON.stringify({
                            status: "confirmed"
                        })
                    });
                }

                setPayStatus("approved");
                setPayDetail("manual_payment");
                const message = isBalancePayment 
                    ? `Pago ${paymentType} registrado exitosamente` 
                    : `Pago ${paymentType} registrado y reserva confirmada`;
                showResult("approved", message);
            } else {
                throw new Error("Error al registrar el pago");
            }
        } catch (err) {
            console.error(`Error en pago ${paymentType}:`, err);
            setError(err?.message || `Error al registrar pago ${paymentType}`);
            showResult("error", err?.message || `Error al registrar pago ${paymentType}`);
        }
    };

    // Pago de prueba directo (sandbox) usando tarjeta APRO
    const payWithTestCard = async () => {
        try {
            setError("");
            const pubKey = import.meta.env.VITE_MP_PUBLIC_KEY;
            const cardBody = {
                card_number: "5031755734530604", // Mastercard APRO
                expiration_month: 11,
                expiration_year: 2030,
                security_code: "123",
                cardholder: { name: "APRO", identification: { type: "DNI", number: "12345678" } },
            };
            const tokenResp = await fetch(
                `https://api.mercadopago.com/v1/card_tokens?public_key=${pubKey}`,
                { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cardBody) }
            );
            const tokenData = await tokenResp.json();
            if (!tokenResp.ok || !tokenData?.id) throw new Error("No se pudo generar card_token");

            // Determinar el monto correcto del pago
            let paymentAmount;
            if (isBalancePayment) {
                // Pago de saldo pendiente
                paymentAmount = balanceInfo.balance_due;
            } else if (payAmount !== null) {
                // Pago de seña (monto específico)
                paymentAmount = payAmount;
            } else {
                // Pago total (payAmount es null)
                paymentAmount = reservationData?.total_price || 0;
            }
            
            const payload = {
                reservation_id: reservationId,
                token: tokenData.id,
                payment_method_id: "master",
                installments: 1,
                amount: paymentAmount,
            };
            const url = `${getApiURL()}/api/payments/process-card/`;
            const resp = await fetchWithAuth(url, { method: "POST", body: JSON.stringify(payload) });
            setPayStatus(resp?.status || "submitted");
            setPayDetail(resp?.status_detail || "");
            showResult(resp?.status, resp?.status_detail);
        } catch (e) {
            setError(e?.message || "Error en pago de prueba");
            showResult("error", e?.message);
        }
    };

    // Pago con formulario propio (Checkout API simple)
    const payWithForm = async () => {
        try {
            setError("");
            if (!ccNumber || !ccMonth || !ccYear || !ccCvv || !ccName || !docNumber) {
                setError("Completa los datos de la tarjeta");
                return;
            }
            const pubKey = import.meta.env.VITE_MP_PUBLIC_KEY;
            const cardBody = {
                card_number: String(ccNumber).replace(/\s+/g, ""),
                expiration_month: Number(ccMonth),
                expiration_year: Number(ccYear),
                security_code: String(ccCvv),
                cardholder: { name: ccName, identification: { type: docType, number: docNumber } },
            };
            const tokenResp = await fetch(
                `https://api.mercadopago.com/v1/card_tokens?public_key=${pubKey}`,
                { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cardBody) }
            );
            const tokenData = await tokenResp.json();
            if (!tokenResp.ok || !tokenData?.id) throw new Error("No se pudo generar card_token");

            const first = String(cardBody.card_number)[0];
            const method = first === "4" ? "visa" : first === "5" ? "master" : "visa";

            // Determinar el monto correcto del pago
            let paymentAmount;
            if (isBalancePayment) {
                // Pago de saldo pendiente
                paymentAmount = balanceInfo.balance_due;
            } else if (payAmount !== null) {
                // Pago de seña (monto específico)
                paymentAmount = payAmount;
            } else {
                // Pago total (payAmount es null)
                paymentAmount = reservationData?.total_price || 0;
            }

            const payload = {
                reservation_id: reservationId,
                token: tokenData.id,
                payment_method_id: method,
                installments: Number(installments) || 1,
                amount: paymentAmount,
            };
            const url = `${getApiURL()}/api/payments/process-card/`;
            const resp = await fetchWithAuth(url, { method: "POST", body: JSON.stringify(payload) });
            setPayStatus(resp?.status || "submitted");
            setPayDetail(resp?.status_detail || "");
            showResult(resp?.status, resp?.status_detail);
        } catch (e) {
            setError(e?.message || "Error en pago con tarjeta");
            showResult("error", e?.message);
        }
    };

    const translateDetail = (d) => {
        if (!d) return "";
        const map = {
            cc_rejected_insufficient_amount: "Fondos insuficientes",
            cc_rejected_bad_filled_card_number: "Número de tarjeta inválido",
            cc_rejected_bad_filled_date: "Fecha de vencimiento inválida",
            cc_rejected_bad_filled_other: "Datos incompletos o inválidos",
            cc_rejected_bad_filled_security_code: "Código de seguridad inválido",
            cc_rejected_high_risk: "Pago rechazado por política de seguridad",
            cc_rejected_blacklist: "Pago rechazado por prevención de fraude",
            cc_rejected_other_reason: "Pago rechazado por el emisor",
        };
        return map[d] || d;
    };

    const showResult = (status, detail) => {
        const map = {
            approved: { icon: "success", title: "Pago aprobado", text: detail || "accredited" },
            in_process: { icon: "info", title: "Pago en proceso", text: "Te avisaremos cuando se acredite" },
            rejected: { icon: "error", title: "Pago rechazado", text: detail || "Intenta nuevamente" },
            error: { icon: "error", title: "Error", text: detail || "Ocurrió un error" },
        };
        const cfg = map[status] || map.error;
        const palette = {
            approved: { bg: "#16a34a", color: "#ffffff", iconColor: "#ffffff" }, // verde
            in_process: { bg: "#2563eb", color: "#ffffff", iconColor: "#ffffff" }, // azul
            rejected: { bg: "#b91c1c", color: "#ffffff", iconColor: "#ffffff" },   // rojo oscuro
            error: { bg: "#b91c1c", color: "#ffffff", iconColor: "#ffffff" },      // rojo oscuro
        };
        const colors = palette[status] || palette.error;
        const approvedBtn = status === "approved";
        const anim = status === "approved"
            ? { show: "animate__zoomIn", hide: "animate__zoomOut" }
            : status === "rejected" || status === "error"
            ? { show: "animate__shakeX", hide: "animate__fadeOutDown" }
            : { show: "animate__fadeInDown", hide: "animate__fadeOutUp" };
        Swal.fire({
            icon: cfg.icon,
            title: cfg.title,
            text: translateDetail(cfg.text),
            confirmButtonText: "Aceptar",
            allowOutsideClick: false,
            allowEscapeKey: false,
            allowEnterKey: true,
            background: colors.bg,
            color: colors.color,
            iconColor: colors.iconColor,
            buttonsStyling: true,
            confirmButtonColor: approvedBtn ? "#ffffff" : "#16a34a",
            showClass: {
                popup: `animate__animated ${anim.show}`,
                icon: `animate__animated ${anim.show}`,
                backdrop: "animate__animated animate__fadeIn",
            },
            hideClass: {
                popup: `animate__animated ${anim.hide}`,
                backdrop: "animate__animated animate__fadeOut",
            },
            didOpen: () => {
                const c = Swal.getContainer();
                if (c) {
                    c.style.zIndex = "10000";
                    // Blur del fondo
                    c.style.backdropFilter = "blur(6px)";
                    c.style.background = "rgba(0,0,0,0.25)";
                    c.style.webkitBackdropFilter = "blur(6px)";
                }
                const p = Swal.getPopup();
                if (p) p.style.borderRadius = "18px";
                const btn = Swal.getConfirmButton();
                if (btn) {
                    btn.style.backgroundColor = approvedBtn ? "#ffffff" : "#16a34a";
                    btn.style.color = approvedBtn ? "#166534" : "#ffffff";
                    btn.style.borderRadius = "9999px";
                    btn.style.border = approvedBtn ? "1px solid #166534" : "none";
                }
            },
        }).then((r) => {
            if (r.isConfirmed && status === "approved") {
                onPaid?.({ ok: true });
                onClose?.();
            }
        });
    };

    // Reset estados al cerrar
    useEffect(() => {
        if (!isOpen) {
            setPref(null);
            setError("");
            setReservationData(null);
            setPolicy(null);
            setDepositInfo(null);
            setPayAmount(null);
            setStep(isBalancePayment ? "select" : "amount");
        } else {
            // Cuando se abre el modal, establecer el step inicial
            setStep(isBalancePayment ? "select" : "amount");
        }
    }, [isOpen, isBalancePayment]);

    // Cargar datos de la reserva y la política cuando se abre
    useEffect(() => {
        if (!isOpen || !reservationId) return;
        let cancelled = false;
        (async () => {
            try {
                setError("");
                
                if (isBalancePayment) {
                    // Para pago de saldo pendiente, usar la información proporcionada
                    setReservationData({ 
                        hotel: null, // No necesitamos cargar esto para saldo pendiente
                        total_price: balanceInfo.total_reservation 
                    });
                    setStep("select");
                    setPayAmount(balanceInfo.balance_due);
                } else {
                    // Para confirmación inicial, cargar datos normalmente
                    const res = await fetchWithAuth(`${getApiURL()}/api/reservations/${reservationId}/`);
                    if (cancelled) return;
                    setReservationData({ hotel: res?.hotel, total_price: res?.total_price });
                    
                    // Obtener política activa
                    if (res?.hotel) {
                        const pol = await paymentPolicyService.getActivePolicyForHotel(res.hotel);
                        if (cancelled) return;
                        setPolicy(pol);
                        if (pol && res?.total_price != null) {
                            const dep = paymentPolicyService.calculateDeposit(pol, Number(res.total_price));
                            setDepositInfo(dep);
                            // Si no hay depósito requerido, ir directo a selección de método
                            if (!dep?.required || pol?.allow_deposit === false) {
                                setStep("select");
                                setPayAmount(null); // total
                            }
                        } else {
                            setStep("select");
                        }
                    } else {
                        setStep("select");
                    }
                }
            } catch (e) {
                if (!cancelled) {
                    setError(e?.message || "Error cargando datos de la reserva");
                    setStep("select");
                }
            }
        })();
        return () => { cancelled = true; };
    }, [isOpen, reservationId, isBalancePayment, balanceInfo]);

    // Crear preferencia solo cuando se selecciona tarjeta (no para métodos manuales)
    useEffect(() => {
        if (!isOpen || !reservationId) return;
        // Solo crear preferencia cuando se selecciona tarjeta en el step form
        if (step !== "form" || paymentMethod !== "card") return;
        let cancelled = false;
        (async () => {
            try {
                setLoading(true);
                setError("");
                setPref(null);
                const resp = await createPreference({
                    reservationId,
                    ...(isBalancePayment ? { amount: balanceInfo.balance_due } : (payAmount != null ? { amount: payAmount } : {})),
                });
                if (!cancelled) setPref(resp);
            } catch (e) {
                if (!cancelled) setError(e.message || "Error al crear preferencia");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [isOpen, reservationId, step, paymentMethod, payAmount, isBalancePayment, balanceInfo]);

    // Polling para detectar status=confirmed (solo con preferencia creada)
  useEffect(() => {
        if (!isOpen || !reservationId || !pref?.preference_id) return;
        attemptsRef.current = 0;
    let timer = null;
    let cancelled = false;
    const tick = async () => {
            if (cancelled) return;
            // Evitar consultas cuando la pestaña no está visible
            if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
                timer = setTimeout(tick, 6000);
                return;
            }
      try {
        const url = `${getApiURL()}/api/reservations/${reservationId}/`;
        const res = await fetchWithAuth(url);
        setStatus(res?.status || "");
        if (res?.status === "confirmed") {
                    // Mostrar mensaje y esperar confirmación del usuario
                    setPayStatus((s) => (s || "approved"));
                    setPayDetail((d) => (d || "accredited"));
                    return;
                }
            } catch {}
            // Reintentos acotados
            attemptsRef.current += 1;
            if (!cancelled && attemptsRef.current < 40) {
                timer = setTimeout(tick, 6000); // cada 6s, por ~4min máx
      }
    };
    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
    }, [isOpen, reservationId, pref?.preference_id]);

  return (
    <ModalLayout
      isOpen={isOpen}
            onClose={() => {
                setPref(null);
                setError("");
                onClose && onClose();
            }}
      title={isBalancePayment ? `Pago de Saldo Pendiente - ${balanceInfo.payment_required_at === 'check_in' ? 'Check-in' : 'Check-out'}` : "Pago de reserva"}
      size="lg"
    >
      <div className="space-y-3 p-1">
        {loading && paymentMethod === "card" && step === "form" && pref === null && <SpinnerLoading />}
        {error && <div style={{ color: "red" }}>{error}</div>}
        
        
        {/* Información del saldo pendiente */}
        {isBalancePayment && balanceInfo && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-gray-800 mb-2">Resumen de Pagos</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Total Reserva:</span>
                <span className="font-semibold ml-2">
                  {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(balanceInfo.total_reservation || 0)}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Total Pagado:</span>
                <span className="font-semibold ml-2 text-green-600">
                  {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(balanceInfo.total_paid || 0)}
                </span>
              </div>
              <div className="col-span-2 border-t pt-2">
                <span className="text-gray-600">Saldo Pendiente:</span>
                <span className="font-bold text-lg ml-2 text-red-600">
                  {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(balanceInfo.balance_due || 0)}
                </span>
              </div>
            </div>
          </div>
        )}
                {step === "amount" && !isBalancePayment && (
                    <div className="relative overflow-hidden">
                        <div 
                            className={`transition-all duration-300 ease-in-out ${
                                step === "amount" 
                                    ? "opacity-100 translate-x-0" 
                                    : "opacity-0 -translate-x-full absolute inset-0"
                            }`}
                        >
                            <div className="space-y-3">
                                <div className="text-center">
                                    <h3 className="text-lg font-semibold">¿Qué querés pagar?</h3>
                                    {policy?.name ? (
                                        <div className="text-sm text-gray-600 mt-1">Política: {policy.name}</div>
                                    ) : null}
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-2">
                                    {/* Opción Seña */}
                                    {depositInfo?.required && (policy?.allow_deposit ?? true) && (
                                        <button
                                            onClick={() => { setPayAmount(Number(depositInfo.amount)); setStep("select"); }}
                                            className="w-full flex items-center justify-between cursor-pointer hover:scale-103 p-4 border rounded-lg border-aloja-gray-100 shadow-sm hover:bg-orange-50 transition-all duration-200"
                                        >
                                            <div className="text-left">
                                                <div className="font-semibold text-orange-700">{policy?.name || "Seña"}</div>
                                                <div className="text-xs text-orange-600">Pagar ahora</div>
                                            </div>
                                            <div className="text-right font-bold text-orange-800">
                                                {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(depositInfo.amount) || 0)}
                                            </div>
                                        </button>
                                    )}
                                    {/* Opción Total */}
                                    <button
                                        onClick={() => { setPayAmount(null); setStep("select"); }}
                                        className="w-full flex items-center justify-between cursor-pointer hover:scale-103 p-4 border rounded-lg border-aloja-gray-100 shadow-sm hover:bg-green-50 transition-all duration-200"
                                    >
                                        <div className="text-left">
                                            <div className="font-semibold text-green-700">Pagar Total</div>
                                            <div className="text-xs text-green-600">Saldo completo</div>
                                        </div>
                                        <div className="text-right font-bold text-green-800">
                                            {new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(reservationData?.total_price) || 0)}
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {(step === "select" || step === "form") && (
                    <div className="relative overflow-hidden">
                        {/* Paso 1 - Selección de método */}
                        <div 
                            className={`transition-all duration-300 ease-in-out ${
                                step === "select" 
                                    ? "opacity-100 translate-x-0" 
                                    : "opacity-0 -translate-x-full absolute inset-0"
                            }`}
                        >
                            {/* Header con flecha de volver */}
                            <div className="flex items-center mb-4">
                                {!isBalancePayment && (
                                    <button
                                        onClick={() => setStep("amount")}
                                        className="mr-3 p-1 hover:bg-gray-100 rounded-full transition cursor-pointer"
                                    >
                                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                        </svg>
                                    </button>
                                )}
                                <h3 className="text-lg font-semibold">
                                    {isBalancePayment ? "¿Cómo querés pagar el saldo pendiente?" : "¿Cómo querés pagar?"}
                                </h3>
                            </div>

                            {/* Selector de método de pago */}
                            <div className="space-y-2 p-2">
                                    <button
                                        onClick={() => {
                                            setPaymentMethod("card");
                                            setStep("form");
                                        }}
                                        className="w-full flex items-center cursor-pointer p-3 border rounded-lg border-aloja-gray-100 shadow-sm hover:scale-103 hover:bg-gray-100 transition-all duration-200"
                                    >
                                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                                <CardCreditIcon />
                                            </svg>
                                        </div>
                                        <div className="flex-1 text-left">
                                            <div className="font-medium">Tarjeta Online</div>
                                            <div className="text-sm text-gray-500">Visa, Mastercard, American Express</div>
                                        </div>
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </button>

                                    <button
                                        onClick={() => {
                                            setPaymentMethod("cash");
                                            setStep("form");
                                        }}
                                        className="w-full flex items-center cursor-pointer p-3 border rounded-lg border-aloja-gray-100 shadow-sm hover:scale-103 hover:bg-gray-100 transition-all duration-200"
                                    >
                                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                                <CrashIcon />
                                            </svg>
                                        </div>
                                        <div className="flex-1 text-left">
                                            <div className="font-medium">Efectivo</div>
                                            <div className="text-sm text-gray-500">Pago en efectivo al llegar</div>
                                        </div>
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </button>

                                    <button
                                        onClick={() => {
                                            setPaymentMethod("transfer");
                                            setStep("form");
                                        }}
                                        className="w-full flex items-center cursor-pointer p-3 border rounded-lg border-aloja-gray-100 shadow-sm hover:scale-103 hover:bg-gray-100 transition-all duration-200"
                                    >
                                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                                            <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                                               <TranfCrash />
                                            </svg>
                                        </div>
                                        <div className="flex-1 text-left">
                                            <div className="font-medium">Transferencia</div>
                                            <div className="text-sm text-gray-500">Transferencia bancaria con comprobante</div>
                                        </div>
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </button>

                                    <button
                                        onClick={() => {
                                            setPaymentMethod("pos");
                                            setStep("form");
                                        }}
                                        className="w-full flex items-center cursor-pointer p-3 border rounded-lg border-aloja-gray-100 shadow-sm hover:scale-103 hover:bg-gray-100 transition-all duration-200"
                                    >
                                        <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mr-3">
                                            <svg className="w-5 h-5 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                                                <PostnetIcon />
                                            </svg>
                                        </div>
                                        <div className="flex-1 text-left">
                                            <div className="font-medium">PostNet</div>
                                            <div className="text-sm text-gray-500">Terminal de pago con tarjeta</div>
                                        </div>
                                        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                        </svg>
                                    </button>
                                </div>
                        </div>

                        {/* Paso 2 - Formulario del método seleccionado */}
                        <div 
                            className={`transition-all duration-300 ease-in-out ${
                                step === "form" 
                                    ? "opacity-100 translate-x-0" 
                                    : "opacity-0 translate-x-full absolute inset-0"
                            }`}
                        >
                            {/* Header con flecha de volver */}
                            <div className="flex items-center mb-4">
                                <button
                                    onClick={() => setStep("select")}
                                    className="mr-3 p-1 hover:bg-gray-100 rounded-full transition"
                                >
                                    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                    </svg>
                                </button>
                                <h3 className="text-lg font-semibold">
                                    {paymentMethod === "card" && (isBalancePayment ? "Pagar Saldo con Tarjeta" : "Pagar con Tarjeta")}
                                    {paymentMethod === "cash" && (isBalancePayment ? "Pago de Saldo en Efectivo" : "Pago en Efectivo")}
                                    {paymentMethod === "transfer" && (isBalancePayment ? "Transferencia para Saldo" : "Transferencia Bancaria")}
                                    {paymentMethod === "pos" && (isBalancePayment ? "Pago de Saldo con PostNet" : "Pago con PostNet")}
                                </h3>
                            </div>

                                {/* Formularios según método seleccionado */}
                                {paymentMethod === "card" && pref && (
                                    <PaymentBrick
                                        key={`pb-${reservationId}-${isBalancePayment ? balanceInfo.balance_due : (payAmount || 'total')}-${pref?.preference_id || 'x'}`}
                                        reservationId={reservationId}
                                        amount={isBalancePayment ? balanceInfo.balance_due : (pref?.amount || undefined)}
                                        onSuccess={(resp) => { setPayStatus(resp?.status || "approved"); setPayDetail(resp?.status_detail || "accredited"); showResult(resp?.status, resp?.status_detail); }}
                                        onError={(err) => { setError(err?.message || "Error en el pago"); showResult("error", err?.message); }}
                                    />
                                )}
                                
                                {paymentMethod === "card" && !pref && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <div className="text-center">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                                            <p className="text-sm text-gray-600">Preparando pago con tarjeta...</p>
                                        </div>
                                    </div>
                                )}

                                {paymentMethod === "cash" && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="font-medium mb-2">Pago en Efectivo</h4>
                                        <p className="text-sm text-gray-600 mb-4">
                                            {isBalancePayment 
                                                ? "El huésped pagará el saldo pendiente en efectivo."
                                                : "El huésped pagará en efectivo al llegar al hotel. La reserva quedará confirmada sin pago previo."
                                            }
                                        </p>
                                        <button
                                            onClick={() => registerManualPayment("cash")}
                                            className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition"
                                        >
                                            {isBalancePayment ? "Confirmar Pago de Saldo en Efectivo" : "Confirmar Pago en Efectivo"}
                                        </button>
            </div>
                                )}

                                {paymentMethod === "transfer" && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="font-medium mb-2">Transferencia Bancaria</h4>
                                        <p className="text-sm text-gray-600 mb-4">
                                            {isBalancePayment 
                                                ? "El huésped realizará una transferencia bancaria por el saldo pendiente. Sube el comprobante para confirmar el pago."
                                                : "El huésped realizará una transferencia bancaria. Sube el comprobante para confirmar el pago."
                                            }
                                        </p>
                                        <div className="space-y-3">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Comprobante de Transferencia
                                                </label>
                                                <input
                                                    type="file"
                                                    accept="image/*,.pdf"
                                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Número de Operación
                                                </label>
                                                <input
                                                    type="text"
                                                    placeholder="Ej: 1234567890"
                                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <button
                                                onClick={() => registerManualPayment("transfer")}
                                                className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition"
                                            >
                                                {isBalancePayment ? "Confirmar Transferencia de Saldo" : "Confirmar Transferencia"}
                                            </button>
                                        </div>
        </div>
                                )}

                                {paymentMethod === "pos" && (
                                    <div className="p-4 bg-gray-50 rounded-lg">
                                        <h4 className="font-medium mb-2">Pago con PostNet</h4>
                                        <p className="text-sm text-gray-600 mb-4">
                                            {isBalancePayment 
                                                ? "Procesa el pago del saldo pendiente con la terminal PostNet del hotel."
                                                : "Procesa el pago con la terminal PostNet del hotel."
                                            }
                                        </p>
                                        <div className="space-y-3">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Número de Autorización
                                                </label>
                                                <input
                                                    type="text"
                                                    placeholder="Ej: 123456"
                                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                                    Últimos 4 dígitos de la tarjeta
                                                </label>
                                                <input
                                                    type="text"
                                                    placeholder="Ej: 1234"
                                                    maxLength="4"
                                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                                />
                                            </div>
                                            <button
                                                onClick={() => registerManualPayment("pos")}
                                                className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 transition"
                                            >
                                                {isBalancePayment ? "Confirmar Pago de Saldo PostNet" : "Confirmar Pago PostNet"}
                                            </button>
                                        </div>
        </div>
                                )}
                        </div>
                    </div>
                )}
      </div>
    </ModalLayout>
  );
}