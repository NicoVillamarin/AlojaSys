// Configuración runtime para producción (no afecta localhost)
(function () {
  try {
    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1';
    if (!isLocal) {
      window.__API_URL__ = window.__API_URL__;
      // Mercado Pago:
      // No seteamos una public key por defecto acá para evitar mezclar ambientes (TEST vs PROD).
      // En producción, configurá `VITE_MP_PUBLIC_KEY` (build-time) o inyectá `window.__MP_PUBLIC_KEY__` en runtime.
    }
  } catch (_) {
    // noop
  }
})();
