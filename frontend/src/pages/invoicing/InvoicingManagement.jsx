import { useTranslation } from 'react-i18next'
import InvoicesList from './InvoicesList'

export default function InvoicingManagement() {
  const { t } = useTranslation()

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Gestión Fiscal</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Factura Electrónica</h1>
          <p className="text-sm text-gray-600 mt-1">
            Gestiona facturas electrónicas argentinas con integración AFIP
          </p>
        </div>
      </div>

      <InvoicesList />
    </div>
  )
}
