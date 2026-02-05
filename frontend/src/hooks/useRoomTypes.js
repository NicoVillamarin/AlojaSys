import { useMemo } from 'react'
import { useList } from 'src/hooks/useList'

/**
 * useRoomTypes({ includeInactive, enabled })
 * Devuelve catálogo de tipos de habitación desde /api/room-types/
 * y helpers para label/opciones (evita hardcode single/double/...).
 */
export const useRoomTypes = ({ includeInactive = false, enabled = true } = {}) => {
  const { results, isPending, refetch } = useList({
    resource: 'room-types',
    params: includeInactive ? {} : { is_active: 'true' },
    enabled,
  })

  const roomTypes = results || []

  const roomTypeMap = useMemo(() => {
    const m = new Map()
    for (const rt of roomTypes) {
      if (rt?.code) m.set(String(rt.code), rt)
    }
    return m
  }, [roomTypes])

  const getRoomTypeLabel = (code) => {
    const key = code != null ? String(code) : ''
    if (!key) return ''
    const rt = roomTypeMap.get(key)
    if (!rt) return key
    return rt.alias || rt.name || rt.code || key
  }

  const roomTypeOptions = useMemo(() => {
    const list = [...roomTypes]
    list.sort((a, b) => {
      const ao = Number(a?.sort_order ?? 0)
      const bo = Number(b?.sort_order ?? 0)
      if (ao !== bo) return ao - bo
      return String(a?.name ?? '').localeCompare(String(b?.name ?? ''))
    })
    return list
      .map((rt) => {
        const code = rt?.code
        if (!code) return null
        const name = rt?.name || code
        const alias = rt?.alias
        const isActive = rt?.is_active !== false
        let label = alias ? `${alias} — ${name}` : String(name)
        if (!isActive) label = `${label} (inactivo)`
        return { value: code, label }
      })
      .filter(Boolean)
  }, [roomTypes])

  return {
    roomTypes,
    roomTypesLoading: isPending,
    refetchRoomTypes: refetch,
    roomTypeOptions,
    roomTypeMap,
    getRoomTypeLabel,
  }
}

