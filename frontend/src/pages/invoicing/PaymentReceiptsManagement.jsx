import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation } from 'react-router-dom'
import Tabs from 'src/components/Tabs'
import PaymentReceipts from './PaymentReceipts'
import RefundReceipts from './RefundReceipts'

export default function PaymentReceiptsManagement() {
  const { t } = useTranslation()
  const location = useLocation()
  const [activeTab, setActiveTab] = useState('payment-receipts')

  const tabs = [
    { id: 'payment-receipts', label: 'Comprobantes de Señas' },
    { id: 'refund-receipts', label: 'Comprobantes de Devoluciones' },
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'payment-receipts':
        return <PaymentReceipts />
      case 'refund-receipts':
        return <RefundReceipts />
      default:
        return <PaymentReceipts />
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-aloja-gray-800/60">Gestión Fiscal</div>
          <h1 className="text-2xl font-semibold text-aloja-navy">Comprobantes</h1>
          <p className="text-sm text-gray-600 mt-1">
            Gestiona comprobantes de pagos y devoluciones
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
