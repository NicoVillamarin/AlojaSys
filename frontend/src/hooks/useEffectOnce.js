import { useEffect, useRef } from 'react'

export const useEffectOnce = (effect) => {
  const ran = useRef(false)
  useEffect(() => {
    if (ran.current) return
    ran.current = true
    return effect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}


