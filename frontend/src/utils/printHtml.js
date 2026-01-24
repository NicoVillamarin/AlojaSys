/**
 * printHtml
 * Utilidad genérica para imprimir contenido HTML.
 *
 * Uso:
 *   printHtml({ title: "Mi reporte", html: "<h1>...</h1>" })
 */
export function printHtml({
  title = "Imprimir",
  html = "",
  css = "",
  targetWindow = null,
  autoPrint = true,
  showPrintButton = true,
  features = "width=980,height=720",
} = {}) {
  // Importante: abrir la ventana en el click (sync) y luego rellenarla.
  // Si se llama después de un await, muchos navegadores bloquean el popup y queda en blanco.
  const w = targetWindow || window.open("", "_blank", features);
  if (!w) {
    throw new Error(
      "No se pudo abrir la ventana de impresión. Revisá si el navegador bloqueó el popup."
    );
  }

  // Mitigación reverse-tabnabbing (sin romper acceso al documento)
  try {
    w.opener = null;
  } catch {
    // noop
  }

  const baseCss = `
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { font-family: Arial, Helvetica, sans-serif; color: #111827; margin: 0; }
    .container { padding: 24px; }
    .title { font-size: 18px; font-weight: 700; margin: 0 0 6px; }
    .meta { font-size: 12px; color: #6b7280; margin-bottom: 16px; }
    .badge { display: inline-block; border: 1px solid #e5e7eb; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #e5e7eb; padding: 8px; font-size: 12px; vertical-align: top; }
    th { background: #f9fafb; text-align: left; }
    .muted { color: #6b7280; }
    .right { text-align: right; }
    .center { text-align: center; }
    .no-print { display: block; margin-bottom: 14px; }
    .btn { display:inline-block; padding:8px 12px; border-radius:8px; border:1px solid #d1d5db; background:#fff; color:#111827; cursor:pointer; }
    @media print {
      .no-print { display: none !important; }
      body { margin: 0; padding: 0; }
      .container { padding: 0; }
      html, body { height: 100%; }
      th { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      @page { 
        margin: 0; 
        size: A4; 
      }
      /* Ocultar headers/footers del navegador */
      @page {
        @top-right { content: ""; }
        @top-left { content: ""; }
        @top-center { content: ""; }
        @bottom-right { content: ""; }
        @bottom-left { content: ""; }
        @bottom-center { content: ""; }
      }
    }
  `;

  const btnHtml = showPrintButton
    ? `<div class="no-print"><button class="btn" onclick="window.print()">Imprimir</button></div>`
    : "";

  const autoPrintScript = autoPrint
    ? `window.addEventListener('load', () => setTimeout(() => window.print(), 50));`
    : "";

  w.document.open();
  w.document.write(`<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    <style>${baseCss}\n${css || ""}</style>
  </head>
  <body>
    <div class="container">
      ${btnHtml}
      ${html || ""}
    </div>
    <script>
      ${autoPrintScript}
    </script>
  </body>
</html>`);
  w.document.close();
  w.focus();

  return w;
}

function escapeHtml(input) {
  return String(input ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

