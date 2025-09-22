import React from 'react'
import DropdownUser from './DropdownUser'
import { NavLink, useLocation } from 'react-router-dom'
const Navbar = () => {

const location = useLocation()
const titleMap = {
  '/': 'Dashboard',
  '/clients': 'Clientes',
  '/reservations': 'Reservas',
  '/rooms': 'Habitaciones',
  '/rates': 'Tarifas',
  '/settings': 'Configuración',
}
const currentTitle = titleMap[location.pathname] || 'AlojaSys'

    return (
        <div className='h-20 flex items-center justify-between px-4 bg-white shadow-sm'>
            <div className='flex items-center gap-4'>
                <div className='text-aloja-navy font-semibold text-lg'>{currentTitle}</div>
                <nav className='hidden md:flex items-center gap-3 text-sm'>
                    <NavLink to="/" end className={({ isActive }) => isActive ? "text-aloja-navy" : "text-aloja-gray-800"}>Inicio</NavLink>
                </nav>
            </div>
            <div className='flex items-center gap-3 text-sm'>
                <DropdownUser />
            </div>
        </div>
    )
}

export default Navbar