import React from 'react'
import DropdownUser from './DropdownUser'
import LanguageSelector from './LanguageSelector'
import { NavLink, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
const Navbar = () => {
  const { t } = useTranslation();
  const location = useLocation();
  
  const titleMap = {
    '/': t('navbar.dashboard'),
    '/clients': t('navbar.clients'),
    '/reservations': t('navbar.reservations'),
    '/rooms': t('navbar.rooms'),
    '/rates': t('navbar.rates'),
    '/settings': t('navbar.settings'),
  }
  const currentTitle = titleMap[location.pathname] || 'AlojaSys'

    return (
        <div className='h-20 flex items-center justify-between px-4 bg-white shadow-sm'>
            <div className='flex items-center gap-4'>
                <div className='text-aloja-navy font-semibold text-lg'>{currentTitle}</div>
                <nav className='hidden md:flex items-center gap-3 text-sm'>
                    <NavLink to="/" end className={({ isActive }) => isActive ? "text-aloja-navy" : "text-aloja-gray-800"}>{t('navbar.home')}</NavLink>
                </nav>
            </div>
            <div className='flex items-center gap-3 text-sm'>
                <LanguageSelector />
                <DropdownUser />
            </div>
        </div>
    )
}

export default Navbar