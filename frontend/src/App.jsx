import { BrowserRouter, Routes, Route, Navigate, useRoutes } from "react-router-dom"
import { useState, useEffect } from "react"
import PrivateRoute from "src/routes/PrivateRoute"
import PublicRoute from "src/routes/PublicRoute"
import Login from "src/pages/Login"
import PaymentReturn from "src/pages/PaymentReturn"
import LoadingScreen from "src/components/LoadingScreen"
import { appRoutes } from "src/routes/routes"
import { ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"
import "src/i18n"

function AppRoutes() {
  return useRoutes(appRoutes)
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true)
  const [hasShownLoading, setHasShownLoading] = useState(false)

  useEffect(() => {
    // Verificar si ya se mostró la pantalla de carga en esta sesión
    const hasShown = sessionStorage.getItem('hasShownLoadingScreen')
    if (hasShown) {
      setIsLoading(false)
      setHasShownLoading(true)
    }
    // No necesitamos timer aquí, el LoadingScreen maneja su propia duración
  }, [])

  const handleLoadingComplete = () => {
    // La transición ya se maneja dentro del LoadingScreen
    setIsLoading(false)
    setHasShownLoading(true)
    sessionStorage.setItem('hasShownLoadingScreen', 'true')
  }

  // Mostrar pantalla de carga solo en la primera visita
  if (isLoading && !hasShownLoading) {
    return <LoadingScreen onComplete={handleLoadingComplete} />
  }

  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          {/* Rutas públicas para retorno de Mercado Pago (no requieren sesión) */}
          <Route path="/payment/:result" element={<PaymentReturn />} />
          <Route path="/*" element={<PrivateRoute><AppRoutes /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
      <ToastContainer />
    </>
  )
}