/**
 * Exporta un array de objetos (JSON) a un archivo Excel (.xlsx).
 * Hace import dinámico de 'xlsx' para no cargarlo en el bundle inicial.
 */
export async function exportJsonToExcel({ rows, filename, sheetName = 'Datos' }) {
  const XLSXModule = await import('xlsx')
  const XLSX = XLSXModule.default ?? XLSXModule

  const ws = XLSX.utils.json_to_sheet(rows || [])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  XLSX.writeFile(wb, filename)
}

