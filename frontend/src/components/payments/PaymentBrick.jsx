import { useEffect, useMemo, useRef } from "react";
import fetchWithAuth from "src/services/fetchWithAuth";
import { getApiURL, getMercadoPagoPublicKey } from "src/services/utils";

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
    
    let cancelled = false;
    
    // Esperar un tick para asegurar que el DOM esté listo
    const timeoutId = setTimeout(() => {
      if (cancelled) return;
      
      const mp = new window.MercadoPago(getMercadoPagoPublicKey(), { locale: "es-AR" });
      const bricksBuilder = mp.bricks();

      // Verificar que el contenedor existe antes de crear el Brick
      const container = document.getElementById(containerId);
      if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
      }

      // limpiar contenedor por si hubo unmount previo con error
      container.innerHTML = "";
      
      // Aplicar estilos para que el botón ocupe todo el ancho
      container.style.width = "100%";

      // Usar el Card Payment Brick directamente para mostrar el formulario de tarjeta
      bricksBuilder.create("cardPayment", containerId, {
      initialization: { amount: Number(amount || 0) || 0 },
      customization: {
        visual: { 
          style: "default",
          customVariables: {
            buttonBackgroundColor: "#2563eb",
            buttonHeight: "48px"
          }
        },
        maxInstallments: 1,
      },
      callbacks: {
        onReady: () => {
          // Aplicar estilos adicionales una vez que el Brick esté listo
          const brickContainer = document.getElementById(containerId);
          if (brickContainer) {
            // Crear un estilo CSS personalizado para forzar el ancho completo
            const style = document.createElement('style');
            style.textContent = `
              #${containerId} button {
                width: 100% !important;
                min-height: 48px !important;
                max-width: none !important;
              }
              #${containerId} .mp-button {
                width: 100% !important;
                min-height: 48px !important;
                max-width: none !important;
              }
              #${containerId} input {
                width: 100% !important;
              }
              #${containerId} .mp-form-control {
                width: 100% !important;
              }
            `;
            document.head.appendChild(style);
            
            // Aplicar estilos directamente también
            const buttons = brickContainer.querySelectorAll('button');
            buttons.forEach(button => {
              button.style.width = "100% !important";
              button.style.minHeight = "48px !important";
              button.style.maxWidth = "none !important";
            });
            
            // Aplicar estilos a los inputs también
            const inputs = brickContainer.querySelectorAll('input');
            inputs.forEach(input => {
              input.style.width = "100% !important";
            });
          }
        },
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
    }, 100); // Pequeño delay para asegurar que el DOM esté listo

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      try { controllerRef.current?.unmount?.(); } catch {}
      controllerRef.current = null;
      try { const el = document.getElementById(containerId); if (el) el.innerHTML = ""; } catch {}
      createdRef.current = false;
    };
  }, [reservationId, amount, containerId]);

  // Efecto adicional para aplicar estilos después del montaje
  useEffect(() => {
    const applyStyles = () => {
      const container = document.getElementById(containerId);
      if (container) {
        const buttons = container.querySelectorAll('button');
        buttons.forEach(button => {
          button.style.width = "100% !important";
          button.style.minHeight = "48px !important";
          button.style.maxWidth = "none !important";
        });
      }
    };

    // Aplicar estilos inmediatamente
    applyStyles();

    // Aplicar estilos después de un pequeño delay para asegurar que el DOM esté listo
    const timeoutId = setTimeout(applyStyles, 500);
    
    // Observer para detectar cambios en el DOM
    const observer = new MutationObserver(applyStyles);
    const container = document.getElementById(containerId);
    if (container) {
      observer.observe(container, { childList: true, subtree: true });
    }

    return () => {
      clearTimeout(timeoutId);
      observer.disconnect();
    };
  }, [containerId]);

  return <div id={containerId} className="w-full" />;
}