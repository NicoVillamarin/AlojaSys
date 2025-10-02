// Configuración runtime para producción (no afecta localhost)
(function () {
  try {
    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1';
    if (!isLocal) {
      window.__API_URL__ = window.__API_URL__ || 'https://alojasys-backend.onrender.com';
    }
  } catch (_) {
    // noop
  }
})();
