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
  const isSuperuser = !!user?.is_superuser

  const { results: enterprise, isPending } = useAction({
    resource: 'enterprises',
    action: enterpriseId ? String(enterpriseId) : undefined,
    enabled: !!enterpriseId,
    staleTime: 0,
  })

  const planFeatures = useMemo(() => {
    if (!enterpriseId) return {}
    return enterprise?.plan_features || {}
  }, [enterprise, enterpriseId])

  const housekeepingEnabled = useMemo(() => {
    // Si tenemos enterprise, respetar el plan siempre (incluso superuser) para que el UI refleje la licencia.
    if (enterpriseId) return !!planFeatures?.housekeeping_advanced
    // Si no hay enterprise (ej: superuser sin perfil/empresa), no podemos inferir plan:
    // por seguridad/licencia, asumimos deshabilitado.
    return false
  }, [planFeatures, enterpriseId, isSuperuser])

  return {
    planFeatures,
    housekeepingEnabled,
    isPending,
  }
}


