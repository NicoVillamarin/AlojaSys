import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMe } from 'src/hooks/useMe'
import { useAuthStore } from 'src/stores/useAuthStore'
import NoUser from '../assets/img/no_client.png'

export default function DropdownUser() {
  const [isOpen, setIsOpen] = React.useState(false)
  const { data: me } = useMe()
  const logout = useAuthStore(s => s.logout)
  const navigate = useNavigate()
  const ref = useRef(null)

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setIsOpen(false) }
    const onEsc = (e) => { if (e.key === 'Escape') setIsOpen(false) }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onEsc)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onEsc)
    }
  }, [])

  const onLogout = () => { logout(); navigate('/login', { replace: true }) }

  const initials = (me?.first_name || me?.username || 'U').slice(0,1).toUpperCase()

  const avatarSrc = me?.profile?.avatar_image_url || NoUser

  return (
    <div className='relative' ref={ref}>
      <button onClick={() => setIsOpen(o=>!o)} className='flex items-center gap-2 rounded-full pl-1 pr-2 py-1 hover:bg-aloja-gray-100'>
        <img src={avatarSrc} alt='avatar' className='w-14 h-14 rounded-full object-cover border-4 border-gray-300' onError={(e)=>{e.currentTarget.src=NoUser}} />
        <span className='font-bold text-aloja-gray-800 hidden sm:block'>{me?.first_name || me?.username || ''}</span>
        <svg className='h-6 w-6 text-aloja-gray-800' viewBox='0 0 20 20' fill='currentColor' aria-hidden>
          <path fillRule='evenodd' d='M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.08 1.04l-4.25 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z' clipRule='evenodd' />
        </svg>
      </button>
      {isOpen && (
        <div className='absolute right-0 mt-1 w-44 rounded-md border border-aloja-gray-100 bg-white shadow-lg z-50'>
          <div className='px-3 py-2 text-xs text-aloja-gray-800/70'>Sesión</div>
          <button onClick={onLogout} className='w-full text-left px-3 py-2 text-sm border-t border-aloja-gray-100 hover:bg-aloja-gray-100'>Cerrar sesión</button>
        </div>
      )}
    </div>
  )
}