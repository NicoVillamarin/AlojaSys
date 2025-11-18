import React from 'react'
import DropdownUser from './DropdownUser'
import LanguageSelector from './LanguageSelector'
import NotificationsBell from './NotificationsBell'
import { NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMe } from 'src/hooks/useMe'
import { useGet } from 'src/hooks/useGet'

const Navbar = ({ onToggleMobile, isMobile }) => {
  const { t } = useTranslation();
  const location = useLocation();
  const {data: me} = useMe();
  const {results: hotels} = useGet({resource: 'enterprises', id: me?.enterprise_ids[0]});
  const titleMap = {
    '/': t('navbar.dashboard'),
    '/clients': t('navbar.clients'),
    '/reservations': t('navbar.reservations'),
    '/rooms': t('navbar.rooms'),
    '/rates': t('navbar.rates'),
    '/settings': t('navbar.settings'),
    '/notificaciones': 'Notificaciones',
  }
  
    return (
        <div className='h-20 flex items-center justify-between px-4 bg-white shadow-sm relative z-40'>
            <div className='flex items-center gap-4'>
                {/* Botón hamburguesa para móvil */}
                {isMobile && (
                    <button
                        onClick={onToggleMobile}
                        className="p-2 rounded-md text-aloja-navy hover:bg-aloja-gray-100 transition-colors"
                        aria-label="Abrir menú"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                )}
                <div className='text-aloja-navy font-semibold text-xl'>{hotels?.legal_name}</div>
                <nav className='hidden md:flex items-center gap-3 text-sm'>
                    <NavLink to="/" end className={({ isActive }) => isActive ? "text-aloja-navy" : "text-aloja-gray-800"}>{t('navbar.home')}</NavLink>
                </nav>
            </div>
            <div className='flex items-center gap-3 text-sm'>
                <NotificationsBell />
                <LanguageSelector />
                <DropdownUser />
            </div>
        </div>
    )
}

export default Navbar