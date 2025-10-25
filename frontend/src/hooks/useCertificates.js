import { useState, useEffect } from 'react'
import { useGet } from './useGet'

export function useCertificates() {
  const [certificates, setCertificates] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const { data, isLoading, error: fetchError } = useGet({
    resource: 'invoicing/certificates/list',
    enabled: true
  })

  useEffect(() => {
    if (data) {
      setCertificates(data.certificates || [])
      setLoading(isLoading)
      setError(fetchError)
    }
  }, [data, isLoading, fetchError])

  const refresh = () => {
    // El hook useGet se refrescará automáticamente
  }

  return {
    certificates,
    loading,
    error,
    refresh
  }
}
