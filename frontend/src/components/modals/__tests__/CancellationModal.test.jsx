import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nextProvider } from 'react-i18next'
import i18n from 'src/i18n'
import CancellationModal from '../CancellationModal'

// Mock del store de autenticación
jest.mock('src/stores/useAuthStore', () => ({
  getState: () => ({
    accessToken: 'mock-token'
  })
}))

// Mock de fetch
global.fetch = jest.fn()

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const TestWrapper = ({ children }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    </QueryClientProvider>
  )
}

const mockReservation = {
  id: 1,
  display_name: 'RES-001',
  guest_name: 'Juan Pérez',
  check_in: '2024-02-01',
  check_out: '2024-02-03',
  total_price: 1000,
  status: 'confirmed'
}

const mockCancellationData = {
  cancellation_rules: {
    type: 'free',
    message: 'Cancelación gratuita hasta 24 horas antes del check-in'
  },
  financial_summary: {
    total_paid: 1000,
    penalty_amount: 0,
    refund_amount: 1000,
    net_refund: 1000
  },
  reservation: {
    id: 1,
    status: 'confirmed',
    check_in: '2024-02-01',
    check_out: '2024-02-03',
    total_price: 1000
  }
}

const mockCancellationRules = {
  applied_cancellation_policy: {
    id: 1,
    name: 'Política Estándar',
    auto_refund_on_cancel: true
  },
  cancellation_rules: {
    type: 'free',
    message: 'Cancelación gratuita hasta 24 horas antes del check-in'
  },
  refund_rules: {
    type: 'full',
    method: 'original_payment'
  }
}

describe('CancellationModal', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  it('renderiza correctamente cuando está cerrado', () => {
    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={false} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )
    
    expect(screen.queryByText('Cancelar Reserva')).not.toBeInTheDocument()
  })

  it('renderiza el estado de carga inicialmente', () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCancellationData
    })

    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )
    
    expect(screen.getByText('Calculando políticas de cancelación...')).toBeInTheDocument()
  })

  it('muestra la información de cancelación cuando se carga', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationRules
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationData
      })

    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Detalles de la Reserva')).toBeInTheDocument()
    })

    expect(screen.getByText('RES-001')).toBeInTheDocument()
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('Cancelación Gratuita')).toBeInTheDocument()
  })

  it('muestra el badge de reembolso automático cuando está habilitado', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationRules
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationData
      })

    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('✓ Reembolso automático disponible')).toBeInTheDocument()
    })
  })

  it('muestra información de reembolso manual cuando no hay soporte automático', async () => {
    const rulesWithoutAutoRefund = {
      ...mockCancellationRules,
      applied_cancellation_policy: {
        ...mockCancellationRules.applied_cancellation_policy,
        auto_refund_on_cancel: false
      }
    }

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => rulesWithoutAutoRefund
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationData
      })

    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('⚠️ Reembolso manual requerido')).toBeInTheDocument()
    })
  })

  it('valida que el motivo de cancelación es obligatorio', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationRules
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationData
      })

    const onClose = jest.fn()
    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={onClose} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Cancelar y solicitar reembolso')).toBeInTheDocument()
    })

    // Intentar confirmar sin motivo
    fireEvent.click(screen.getByText('Cancelar y solicitar reembolso'))
    
    expect(screen.getByText('El motivo de cancelación es obligatorio')).toBeInTheDocument()
  })

  it('tiene atributos de accesibilidad correctos', async () => {
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationRules
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCancellationData
      })

    render(
      <TestWrapper>
        <CancellationModal 
          isOpen={true} 
          onClose={jest.fn()} 
          reservation={mockReservation}
        />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByLabelText('Detalles de la reserva')).toBeInTheDocument()
    })

    expect(screen.getByLabelText('Política de cancelación aplicada')).toBeInTheDocument()
    expect(screen.getByLabelText('Resumen financiero de la cancelación')).toBeInTheDocument()
    expect(screen.getByLabelText('Información sobre devolución automática')).toBeInTheDocument()
  })
})
