import { useEffect, useMemo, useRef } from "react";
import fetchWithAuth from "src/services/fetchWithAuth";
import { getApiURL } from "src/services/utils";

export default function PaymentBrick({ reservationId, amount, onSuccess, onError }) {
  const containerId = useMemo(() => `payment-brick-${Math.random().toString(36).slice(2)}`, []);
  const controllerRef = useRef(null);
  const successRef = useRef(onSuccess);
  const errorRef = useRef(onError);
  const createdRef = useRef(false);

  // Mantener referencias estables para evitar re-crear el Brick en cada render
  useEffect(() => { successRef.current = onSuccess; }, [onSuccess]);
  useEffect(() => { errorRef.current = onError; }, [onError]);

  useEffect(() => {
    if (!window.MercadoPago || createdRef.current) return;
    const mp = new window.MercadoPago(import.meta.env.VITE_MP_PUBLIC_KEY, { locale: "es-AR" });
    const bricksBuilder = mp.bricks();
    let cancelled = false;

    // limpiar contenedor por si hubo unmount previo con error
    try { const el = document.getElementById(containerId); if (el) el.innerHTML = ""; } catch {}

    // Usar el Card Payment Brick directamente para mostrar el formulario de tarjeta
    bricksBuilder.create("cardPayment", containerId, {
      initialization: { amount: Number(amount || 0) || 0 },
      customization: {
        visual: { style: "default" },
        maxInstallments: 1,
      },
      callbacks: {
        onReady: () => {},
        // cardPayment devuelve cardFormData (no { formData })
        onSubmit: (cardFormData) => new Promise(async (resolve, reject) => {
          try {
            if (!cardFormData || !cardFormData.token) {
              throw new Error("Token de tarjeta no generado por el Brick");
            }
            const payload = {
              reservation_id: reservationId,
              token: cardFormData.token,
              payment_method_id: cardFormData.payment_method_id,
              installments: cardFormData.installments || 1,
              amount: amount,
            };
            const url = `${getApiURL()}/api/payments/process-card/`;
            const resp = await fetchWithAuth(url, { method: "POST", body: JSON.stringify(payload) });
            successRef.current?.(resp);
            resolve();
          } catch (e) {
            errorRef.current?.(e);
            reject(e);
          }
        }),
        onError: (error) => errorRef.current?.(error),
      },
    }).then((controller) => {
      if (cancelled) {
        try { controller.unmount?.(); } catch {}
        return;
      }
      controllerRef.current = controller;
      createdRef.current = true;
    }).catch((err) => errorRef.current?.(err));

    return () => {
      cancelled = true;
      try { controllerRef.current?.unmount?.(); } catch {}
      controllerRef.current = null;
      try { const el = document.getElementById(containerId); if (el) el.innerHTML = ""; } catch {}
      createdRef.current = false;
    };
  }, [reservationId, amount, containerId]);

  return <div id={containerId} />;
}