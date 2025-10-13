import { useEffect, useMemo, useRef, forwardRef, useImperativeHandle } from "react";
import { getMercadoPagoPublicKey } from "src/services/utils";

function CheckoutProButtonInner({
  preferenceId,
  locale = "es-AR",
  onReady,
  onError,
}, ref) {
  const containerId = useMemo(
    () => `wallet-brick-${Math.random().toString(36).slice(2)}`,
    []
  );
  const controllerRef = useRef(null);
  const createdRef = useRef(false);

  useImperativeHandle(ref, () => ({
    destroy: () => {
      try {
        controllerRef.current?.unmount?.();
      } catch {}
      controllerRef.current = null;
      createdRef.current = false;
    },
  }));

  useEffect(() => {
    if (!window.MercadoPago || !preferenceId || createdRef.current) return;

    const mp = new window.MercadoPago(
      getMercadoPagoPublicKey(),
      { locale }
    );
    const bricksBuilder = mp.bricks();
    let cancelled = false;

    bricksBuilder
      .create("wallet", containerId, {
        initialization: { preferenceId },
        // Personalización básica
        customization: {
          visual: { style: "flat" },
        },
        callbacks: {
          onReady: () => onReady?.(),
          onError: (error) => onError?.(error),
        },
      })
      .then((controller) => {
        if (cancelled) {
          try { controller.unmount?.(); } catch {}
          return;
        }
        controllerRef.current = controller;
        createdRef.current = true;
      })
      .catch((err) => onError?.(err));

    return () => {
      cancelled = true;
      try { controllerRef.current?.unmount?.(); } catch {}
      controllerRef.current = null;
      createdRef.current = false;
    };
  }, [preferenceId, locale]);

  return <div id={containerId} />;
}

const CheckoutProButton = forwardRef(CheckoutProButtonInner);
export default CheckoutProButton;