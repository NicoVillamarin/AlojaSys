// Configuración runtime para producción (no afecta localhost)
(function () {
  try {
    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1';
    if (!isLocal) {
      window.__API_URL__ = window.__API_URL__ || 'https://alojasys-backend.onrender.com';
      // Configuración de MercadoPago para producción
      window.__MP_PUBLIC_KEY__ = window.__MP_PUBLIC_KEY__ || 'TEST-7b6a1b69-18e6-40e2-b047-e1d3851a85a7';
    }
  } catch (_) {
    // noop
  }
})();
