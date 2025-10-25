import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import Tabs from 'src/components/Tabs'
import Button from 'src/components/Button'
import { useUserHotels } from 'src/hooks/useUserHotels'
import InvoicesList from './InvoicesList'
import PaymentReceipts from './PaymentReceipts'

export default function InvoicingManagement() {
  const { t } = useTranslation()
  const { isSuperuser } = useUserHotels()
  const [activeTab, setActiveTab] = useState('invoices')

  const tabs = [
    { id: 'invoices', label: 'Facturas Electrónicas' },
    { id: 'receipts', label: 'Comprobantes de Señas' },
    { id: 'reports', label: 'Reportes' },
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'invoices':
        return <InvoicesList />
      case 'receipts':
        return <PaymentReceipts />
      case 'reports':
        return (
          <div className="text-center py-10">
            <p className="text-gray-500">Módulo de reportes en desarrollo</p>
          </div>
        )
      default:
        return <InvoicesList />
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Gestión Fiscal</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Facturación y Comprobantes</h1>
          <p className="text-sm text-gray-600 mt-1">
            Gestiona facturas electrónicas y comprobantes de pagos
          </p>
        </div>
      </div>

      <Tabs 
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {renderTabContent()}
    </div>
  )
}
