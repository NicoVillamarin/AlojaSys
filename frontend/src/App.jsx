import { BrowserRouter, Routes, Route, Navigate, useRoutes } from "react-router-dom"
import PrivateRoute from "src/routes/PrivateRoute"
import PublicRoute from "src/routes/PublicRoute"
import Login from "src/pages/Login"
import { appRoutes } from "src/routes/routes"
import { ToastContainer } from "react-toastify"
import "react-toastify/dist/ReactToastify.css"

function AppRoutes() {
  return useRoutes(appRoutes)
}

export default function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/*" element={<PrivateRoute><AppRoutes /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
      <ToastContainer />
    </>
  )
}