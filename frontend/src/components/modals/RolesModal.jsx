import React, { useMemo, useState, useEffect } from 'react'
import { Formik } from 'formik'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import Filter from 'src/components/Filter'
import * as Yup from 'yup'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useList } from 'src/hooks/useList'
import { translatePermissionName, translateAppLabel, PERMISSION_CATEGORIES, getPermissionCategory, filterPermissionsByCategory } from 'src/services/permissionTranslations'

const RolesModal = ({ isOpen, onClose, isEdit = false, role, onSuccess }) => {
  const { t } = useTranslation()
  
  // Estados para filtros
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showTechnical, setShowTechnical] = useState(false) // Mostrar permisos técnicos ocultos
  const [activePreset, setActivePreset] = useState(null) // Preset actualmente activo
  const [instanceKey, setInstanceKey] = useState(0) // Key única para crear nuevos roles
  
  const { mutate: createRole, isPending: creating } = useCreate({
    resource: 'groups',
    onSuccess: (data) => { 
      onSuccess && onSuccess(data)
      onClose && onClose() 
      // Reset filters al cerrar
      setSelectedCategory('all')
      setSearchTerm('')
      setShowTechnical(false)
      setActivePreset(null)
    },
  })
  
  const { mutate: updateRole, isPending: updating } = useUpdate({
    resource: 'groups',
    onSuccess: (data) => { 
      onSuccess && onSuccess(data)
      onClose && onClose() 
      // Reset filters al cerrar
      setSelectedCategory('all')
      setSearchTerm('')
      setShowTechnical(false)
      setActivePreset(null)
    },
  })

  // Obtener todos los permisos disponibles usando useList
  const { results: permissions, isPending: loadingPermissions } = useList({
    resource: 'permissions',
    params: {},
    enabled: isOpen, // Solo cargar cuando el modal esté abierto
  })

  // Filtrar permisos por categoría y búsqueda (ocultando técnicos por defecto)
  const filteredPermissions = useMemo(() => {
    return filterPermissionsByCategory(permissions || [], selectedCategory, searchTerm, !showTechnical)
  }, [permissions, selectedCategory, searchTerm, showTechnical])

  // Agrupar permisos filtrados por app para mostrar mejor
  const groupedPermissions = useMemo(() => {
    if (!filteredPermissions || filteredPermissions.length === 0) return {}
    
    const grouped = {}
    filteredPermissions.forEach(perm => {
      const app = perm.permission?.split('.')[0] || 'other'
      if (!grouped[app]) grouped[app] = []
      grouped[app].push(perm)
    })
    
    // Ordenar por nombre de app
    return Object.keys(grouped)
      .sort()
      .reduce((acc, app) => {
        acc[app] = grouped[app].sort((a, b) => 
          (a.permission || '').localeCompare(b.permission || '')
        )
        return acc
      }, {})
  }, [filteredPermissions])
  
  // Función para obtener el nombre traducido de la app
  const getTranslatedAppName = (app) => {
    return translateAppLabel(app)
  }
  
  // Presets de roles comunes hoteleros con criterio hotelero
  const rolePresets = useMemo(() => {
    if (!permissions || permissions.length === 0) return {}
    
    return {
      recepcionista: {
        name: 'Recepcionista',
        description: 'Atención al cliente, check-in, check-out y reservas',
        permissions: permissions
          .filter(p => {
            if (!p || !p.permission || !p.codename) return false
            
            const appLabel = (p.permission || '').split('.')[0]?.toLowerCase() || ''
            const codename = (p.codename || '').toLowerCase()
            const permission = (p.permission || '').toLowerCase()
            
            // Reservas: ver, agregar, modificar (pero no eliminar)
            if (appLabel === 'reservations') {
              return codename.includes('view') || 
                     codename.includes('add') || 
                     codename.includes('change')
            }
            // Habitaciones: solo ver estado
            if (appLabel === 'rooms') {
              return codename.includes('view')
            }
            // Pagos: ver y agregar (registrar pagos)
            if (appLabel === 'payments') {
              return codename.includes('view') || codename.includes('add')
            }
            // Calendario: ver disponibilidad
            if (appLabel === 'calendar') {
              return codename.includes('view')
            }
            // Dashboard: ver métricas
            if (appLabel === 'dashboard') {
              return codename.includes('view')
            }
            // Usuarios: ver para información de huéspedes
            if (appLabel === 'users' && codename.includes('view')) {
              return true
            }
            // Hoteles: ver para seleccionar
            if (appLabel === 'core' && codename.includes('hotel') && codename.includes('view')) {
              return true
            }
            return false
          })
          .map(p => p.id)
      },
      administrador: {
        name: 'Administrador',
        description: 'Acceso completo al sistema',
        permissions: permissions.map(p => p.id)
      },
      gerente: {
        name: 'Gerente',
        description: 'Gestión operativa completa (sin configuración técnica del sistema)',
        permissions: permissions
          .filter(p => {
            const cat = getPermissionCategory(p)
            const codename = (p.codename || '').toLowerCase()
            // Excluir solo administración técnica (permisos, grupos técnicos, sesiones, log entries)
            if (cat === 'ADMINISTRATION') {
              // Permitir ver grupos pero no modificarlos técnicamente
              return codename.includes('view') && (
                codename.includes('group') || 
                codename.includes('user') ||
                codename.includes('permission')
              )
            }
            // Todo lo demás sí
            return true
          })
          .map(p => p.id)
      },
      contador: {
        name: 'Contador',
        description: 'Facturación, pagos, reportes financieros y conciliación',
        permissions: permissions
          .filter(p => {
            if (!p || !p.permission || !p.codename) return false
            
            const appLabel = (p.permission || '').split('.')[0]?.toLowerCase() || ''
            const codename = (p.codename || '').toLowerCase()
            
            // Facturación completa
            if (appLabel === 'invoicing') return true
            // Pagos: ver y gestionar todo
            if (appLabel === 'payments') return true
            // Dashboard: métricas financieras
            if (appLabel === 'dashboard') return true
            // Reservas: solo ver (para consultar facturación)
            if (appLabel === 'reservations' && codename.includes('view')) {
              return true
            }
            // Hoteles: ver para seleccionar en facturación
            if (appLabel === 'core' && codename.includes('hotel') && codename.includes('view')) {
              return true
            }
            return false
          })
          .map(p => p.id)
      },
      personal_limpieza: {
        name: 'Personal de Limpieza',
        description: 'Solo ver tareas de limpieza (sin crear, editar, eliminar ni acceder a configuraciones)',
        permissions: permissions
          .filter(p => {
            if (!p || !p.permission || !p.codename) return false
            
            const appLabel = (p.permission || '').split('.')[0]?.toLowerCase() || ''
            const codename = (p.codename || '').toLowerCase()
            
            // Housekeeping: solo acceso al módulo y ver tareas
            if (appLabel === 'housekeeping') {
              // Solo acceso al módulo (permite ver la página principal)
              if (codename === 'access_housekeeping') {
                return true
              }
              // Solo view de tareas (housekeepingtask), NO add, change, delete
              // Excluir: tasktemplate, checklist, cleaningzone, cleaningstaff, housekeepingconfig
              if (codename === 'view_housekeepingtask') {
                return true
              }
              // Excluir todos los demás permisos de housekeeping (add, change, delete, configuraciones)
              return false
            }
            // Habitaciones: solo ver estado (para saber qué limpiar)
            if (appLabel === 'rooms' && codename === 'view_room') {
              return true
            }
            return false
          })
          .map(p => p.id)
      },
      comandanta: {
        name: 'Comandanta',
        description: 'Gestión completa de tareas: ver, crear, editar, eliminar (sin acceder a configuraciones)',
        permissions: permissions
          .filter(p => {
            if (!p || !p.permission || !p.codename) return false
            
            const appLabel = (p.permission || '').split('.')[0]?.toLowerCase() || ''
            const codename = (p.codename || '').toLowerCase()
            
            // Housekeeping: solo permisos de tareas (add, change, delete, view, access, manage_all)
            // NO incluir permisos de configuraciones (tasktemplate, checklist, cleaningzone, cleaningstaff, housekeepingconfig)
            if (appLabel === 'housekeeping') {
              // Acceso al módulo
              if (codename === 'access_housekeeping') {
                return true
              }
              // Permisos de tareas (housekeepingtask)
              if (codename === 'view_housekeepingtask' || 
                  codename === 'add_housekeepingtask' ||
                  codename === 'change_housekeepingtask' ||
                  codename === 'delete_housekeepingtask' ||
                  codename === 'manage_all_tasks') {
                return true
              }
              // Excluir permisos de configuraciones
              return false
            }
            // Habitaciones: ver y modificar estado (para marcar como limpias)
            if (appLabel === 'rooms') {
              return codename.includes('view') || codename.includes('change')
            }
            // Reservas: ver para conocer ocupación y check-outs
            if (appLabel === 'reservations' && codename.includes('view')) {
              return true
            }
            return false
          })
          .map(p => p.id)
      },
      supervisor: {
        name: 'Supervisor',
        description: 'Supervisión de operaciones y reportes',
        permissions: permissions
          .filter(p => {
            const cat = getPermissionCategory(p)
            const codename = (p.codename || '').toLowerCase()
            // Ver todo pero modificar solo operativo (no configuración)
            if (cat === 'ADMINISTRATION') {
              return codename.includes('view') && codename.includes('user')
            }
            // Todo lo demás: ver y modificar
            return codename.includes('view') || codename.includes('change')
          })
          .map(p => p.id)
      },
    }
  }, [permissions])
  
  const initialValues = {
    name: role?.name ?? '',
    permissions: role?.permissions?.map(p => p.id) || [],
  }

  const validationSchema = Yup.object().shape({
    name: Yup.string()
      .required(t('roles_modal.name_required'))
      .min(2, t('roles_modal.name_min')),
    permissions: Yup.array()
      .min(1, t('roles_modal.permissions_required')),
  })

  // Resetear estados de filtros cuando cambia el modal o el rol
  useEffect(() => {
    if (isOpen) {
      setSelectedCategory('all')
      setSearchTerm('')
      setShowTechnical(false)
      setActivePreset(null)
      
      // Incrementar instanceKey cuando se abre el modal para crear (para forzar nueva instancia)
      if (!isEdit) {
        setInstanceKey(prev => prev + 1)
      }
    }
  }, [isOpen, role?.id, isEdit])

  return (
    <Formik
      key={isEdit ? `edit-${role?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={(values) => {
        const payload = {
          name: values.name || undefined,
          permissions: values.permissions || [],
        }
        
        if (isEdit && role?.id) {
          updateRole({ id: role.id, body: payload })
        } else {
          createRole(payload)
        }
      }}
    >
      {({ values, handleSubmit, errors, touched, setFieldValue }) => {
        // Ref para rastrear si se modificó manualmente (no desde preset)
        const wasManuallyModified = React.useRef(false)
        
        // Aplicar preset (debe estar dentro del render de Formik para tener acceso a setFieldValue)
        const applyPreset = (presetKey) => {
          const preset = rolePresets[presetKey]
          if (preset && preset.permissions && preset.permissions.length > 0) {
            // Asegurar que los IDs sean números
            const permissionIds = preset.permissions
              .map(id => Number(id))
              .filter(id => !isNaN(id))
            
            // Si no hay IDs válidos, no hacer nada
            if (permissionIds.length === 0) {
              console.warn(`Preset ${presetKey} no tiene permisos válidos`)
              return
            }
            
            // Marcar que NO fue modificado manualmente (viene de preset)
            wasManuallyModified.current = false
            
            // Marcar el preset como activo
            setActivePreset(presetKey)
            
            // Aplicar los permisos
            setFieldValue('permissions', permissionIds, false) // false = no validar inmediatamente
          } else {
            console.warn(`Preset ${presetKey} no encontrado o sin permisos`, preset)
          }
        }
        
        // Manejar cambios manuales en checkboxes de permisos
        const handlePermissionToggle = (permId, isChecked) => {
          // Marcar que fue modificado manualmente
          wasManuallyModified.current = true
          
          const currentPerms = [...values.permissions]
          if (isChecked) {
            if (!currentPerms.includes(permId)) {
              currentPerms.push(permId)
            }
          } else {
            const index = currentPerms.indexOf(permId)
            if (index > -1) {
              currentPerms.splice(index, 1)
            }
          }
          
          setFieldValue('permissions', currentPerms)
          
          // Solo verificar preset si fue modificado manualmente Y después de un delay
          // para dar tiempo a que el usuario termine de hacer cambios
          setTimeout(() => {
            if (wasManuallyModified.current) {
              checkActivePreset()
            }
          }, 500)
        }
        
        // Función auxiliar para normalizar arrays de IDs para comparación
        const normalizeIds = (ids) => {
          return [...new Set(ids.map(id => Number(id)).filter(id => !isNaN(id)))].sort((a, b) => a - b)
        }
        
        // Verificar si el preset actual coincide con los permisos seleccionados
        // Solo se llama cuando hay cambios manuales
        const checkActivePreset = () => {
          if (!wasManuallyModified.current) {
            return // No verificar si no fue modificado manualmente
          }
          
          if (!values.permissions || values.permissions.length === 0) {
            setActivePreset(null)
            return
          }
          
          const currentIds = normalizeIds(values.permissions)
          
          // Comparar con cada preset
          for (const [key, preset] of Object.entries(rolePresets)) {
            if (!preset || !preset.permissions || preset.permissions.length === 0) continue
            
            const presetIds = normalizeIds(preset.permissions)
            
            // Comparación: verificar que tienen el mismo tamaño y los mismos elementos
            if (currentIds.length === presetIds.length) {
              const allMatch = currentIds.every((id, index) => id === presetIds[index])
              
              if (allMatch) {
                // Coinciden exactamente
                setActivePreset(key)
                wasManuallyModified.current = false // Resetear después de encontrar coincidencia
                return
              }
            }
          }
          
          // No coincide con ningún preset
          setActivePreset(null)
        }
        
        // Verificar preset al cargar si estamos editando un rol existente
        useEffect(() => {
          if (isEdit && role?.permissions && role.permissions.length > 0) {
            // Pequeño delay para asegurar que todo esté inicializado
            setTimeout(() => {
              checkActivePreset()
            }, 200)
          }
          // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [isEdit, role?.id])
        
        return (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('roles_modal.edit_role') : t('roles_modal.create_role')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('roles_modal.save_changes') : t('roles_modal.create_role_btn')}
          cancelText={t('roles_modal.cancel')}
          submitDisabled={creating || updating || loadingPermissions}
          submitLoading={creating || updating}
          size='lg'
        >
          <div className='grid grid-cols-1 gap-4 lg:gap-5'>
            <InputText 
              title={`${t('roles_modal.name')} *`} 
              name='name' 
              placeholder={t('roles_modal.name_placeholder')}
            />
            
            {touched.name && errors.name && (
              <p className='text-xs text-red-600 -mt-2'>{errors.name}</p>
            )}

            <div>
              <label className='block text-sm font-medium text-aloja-gray-800 mb-3'>
                {t('roles_modal.permissions')} *
              </label>

              {/* Filtros y presets */}
              {!loadingPermissions && permissions && permissions.length > 0 && (
                <Filter title={t('roles_modal.filters_and_presets')} className='mb-4'>
                  <div className='space-y-3'>
                    {/* Búsqueda */}
                    <div className='relative'>
                      <span className='pointer-events-none absolute inset-y-0 left-2 flex items-center text-aloja-gray-800/60'>
                        <svg className='w-4 h-4' viewBox='0 0 20 20' fill='currentColor' aria-hidden='true'>
                          <path fillRule='evenodd' d='M12.9 14.32a8 8 0 111.414-1.414l3.387 3.387a1 1 0 01-1.414 1.414l-3.387-3.387zM14 8a6 6 0 11-12 0 6 6 0 0112 0z' clipRule='evenodd' />
                        </svg>
                      </span>
                      <input
                        type='text'
                        placeholder={t('roles_modal.search_permissions_placeholder')}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className='w-full border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg pl-8 pr-3 py-2 text-sm transition-all'
                      />
                      {searchTerm && (
                        <button
                          type='button'
                          onClick={() => setSearchTerm('')}
                          className='absolute inset-y-0 right-1 my-1 px-2 rounded-md text-xs text-aloja-gray-800/70 hover:bg-gray-100'
                        >
                          ✕
                        </button>
                      )}
                    </div>

                    {/* Filtro por categoría */}
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800 mb-2'>
                        {t('roles_modal.filter_by_category')}
                      </label>
                      <div className='flex flex-wrap gap-2'>
                        <button
                          type='button'
                          onClick={() => setSelectedCategory('all')}
                          className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                            selectedCategory === 'all'
                              ? 'bg-aloja-navy text-white border-aloja-navy'
                              : 'bg-white text-aloja-gray-800 border-gray-300 hover:border-aloja-navy/50'
                          }`}
                        >
                          {t('roles_modal.all_categories')}
                        </button>
                        {Object.values(PERMISSION_CATEGORIES).map(category => (
                          <button
                            key={category.id}
                            type='button'
                            onClick={() => setSelectedCategory(category.id)}
                            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                              selectedCategory === category.id
                                ? 'bg-aloja-navy text-white border-aloja-navy'
                                : 'bg-white text-aloja-gray-800 border-gray-300 hover:border-aloja-navy/50'
                            }`}
                            title={category.description}
                          >
                            {category.name}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Presets de roles */}
                    <div>
                      <label className='block text-xs font-medium text-aloja-gray-800 mb-2'>
                        {t('roles_modal.role_presets')}
                      </label>
                      <div className='flex flex-wrap gap-2'>
                        {Object.entries(rolePresets).map(([key, preset]) => {
                          const isActive = activePreset === key
                          return (
                            <button
                              key={key}
                              type='button'
                              onClick={() => applyPreset(key)}
                              className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
                                isActive
                                  ? 'bg-aloja-navy text-white border-aloja-navy shadow-md'
                                  : 'bg-white text-aloja-gray-800 border-gray-300 hover:border-aloja-navy/50 hover:bg-aloja-navy/5'
                              }`}
                              title={preset.description}
                            >
                              {preset.name}
                              {isActive && ' ✓'}
                            </button>
                          )
                        })}
                      </div>
                    </div>

                    {/* Opción para mostrar permisos técnicos (avanzado) */}
                    <div className='pt-2 border-t border-gray-200'>
                      <label className='flex items-center gap-2 cursor-pointer'>
                        <input
                          type='checkbox'
                          checked={showTechnical}
                          onChange={(e) => setShowTechnical(e.target.checked)}
                          className='w-4 h-4 text-aloja-navy border-gray-300 rounded focus:ring-aloja-navy'
                        />
                        <span className='text-xs text-aloja-gray-800'>
                          {t('roles_modal.show_technical_permissions')}
                        </span>
                      </label>
                      <p className='text-xs text-aloja-gray-800/60 ml-6 mt-1'>
                        {t('roles_modal.show_technical_permissions_desc')}
                      </p>
                    </div>
                  </div>
                </Filter>
              )}

              {/* Contador de permisos seleccionados */}
              {!loadingPermissions && values.permissions && values.permissions.length > 0 && (
                <div className='mb-2 text-xs'>
                  <span className='font-medium text-aloja-navy'>
                    {values.permissions.length === 1 
                      ? t('roles_modal.selected_permissions_count', { count: 1 })
                      : t('roles_modal.selected_permissions_count_plural', { count: values.permissions.length })
                    }
                  </span>
                </div>
              )}

              {loadingPermissions ? (
                <div className='p-8 text-center text-aloja-gray-800/60'>
                  {t('roles_modal.loading_permissions')}
                </div>
              ) : (
                <div className='border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto bg-gray-50'>
                  {Object.keys(groupedPermissions).length === 0 ? (
                    <div className='text-sm text-aloja-gray-800/60 text-center py-8'>
                      <p className='mb-2'>{t('roles_modal.no_permissions_found')}</p>
                      {(selectedCategory !== 'all' || searchTerm) && (
                        <button
                          type='button'
                          onClick={() => {
                            setSelectedCategory('all')
                            setSearchTerm('')
                          }}
                          className='text-xs text-aloja-navy hover:underline'
                        >
                          {t('roles_modal.clear_filters')}
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className='space-y-4'>
                      {Object.entries(groupedPermissions).map(([app, perms]) => (
                        <div key={app} className='border-b border-gray-200 last:border-b-0 pb-3 last:pb-0'>
                          <h4 className='text-sm font-semibold text-aloja-navy mb-2 uppercase'>
                            {getTranslatedAppName(app)}
                          </h4>
                          <div className='grid grid-cols-1 md:grid-cols-2 gap-2 ml-2'>
                            {perms.map((perm) => {
                              const isChecked = values.permissions.includes(perm.id)
  return (
                                <label
                                  key={perm.id}
                                  className='flex items-center gap-2 p-2 rounded hover:bg-gray-100 cursor-pointer'
                                >
                                  <input
                                    type='checkbox'
                                    checked={isChecked}
                                    onChange={(e) => {
                                      handlePermissionToggle(perm.id, e.target.checked)
                                    }}
                                    className='w-4 h-4 text-aloja-navy border-gray-300 rounded focus:ring-aloja-navy'
                                  />
                                  <span className='text-sm text-aloja-gray-800'>
                                    {translatePermissionName(perm.name) || perm.permission || `ID: ${perm.id}`}
                                  </span>
                                </label>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {touched.permissions && errors.permissions && (
                <p className='mt-2 text-xs text-red-600'>{errors.permissions}</p>
              )}
            </div>
          </div>
        </ModalLayout>
        )
      }}
    </Formik>
  )
}

export default RolesModal
