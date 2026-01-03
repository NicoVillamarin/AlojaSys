import { useMemo } from 'react'
import { useAuthStore } from 'src/stores/useAuthStore'
import { useAction } from 'src/hooks/useAction'

/**
 * Obtiene features efectivos del plan (plan_features) desde Enterprise.
 * Se usa para ocultar/mostrar módulos según plan comercial.
 */
export const usePlanFeatures = () => {
  const { user } = useAuthStore()
  const enterpriseId = user?.enterprise?.id
  const mePlanFeatures = user?.enterprise?.plan_features
  const isSuperuser = !!user?.is_superuser

  // Fallback: si no tenemos plan_features en /api/me/ (por alguna razón),
  // intentamos pedir la enterprise (puede fallar si el usuario no tiene permisos de enterprises).
  const { results: enterprise, isPending } = useAction({
    resource: 'enterprises',
    action: enterpriseId ? String(enterpriseId) : undefined,
    enabled: !!enterpriseId,
    staleTime: 0,
  })

  const planFeatures = useMemo(() => {
    // Superuser sin empresa: en modo admin mostramos todo (no aplicamos gating por plan).
    if (!enterpriseId && isSuperuser) {
      return {
        housekeeping_advanced: true,
        afip: true,
        mercado_pago: true,
        whatsapp_bot: true,
        otas: true,
        bank_reconciliation: true,
      }
    }
    if (!enterpriseId) return {}
    if (mePlanFeatures && typeof mePlanFeatures === 'object') return mePlanFeatures
    return enterprise?.plan_features || {}
  }, [enterprise, enterpriseId, mePlanFeatures, isSuperuser])

  const housekeepingEnabled = useMemo(() => {
    // Si tenemos enterprise, respetar el plan siempre (incluso superuser) para que el UI refleje la licencia.
    if (enterpriseId) return !!planFeatures?.housekeeping_advanced
    // Superuser sin empresa: modo admin => habilitado.
    if (isSuperuser) return true
    // Usuario sin empresa: por seguridad/licencia, deshabilitado.
    return false
  }, [planFeatures, enterpriseId, isSuperuser])

  return {
    planFeatures,
    housekeepingEnabled,
    isPending,
  }
}


