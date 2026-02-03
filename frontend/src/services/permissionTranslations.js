/**
 * Diccionario de traducciones para nombres de permisos de Django
 * Convierte nombres en inglés (ej: "Can view Hotel") al español
 */

// Traducciones de nombres de apps (app_label)
const APP_LABEL_TRANSLATIONS = {
  'admin': 'Administración',
  'auth': 'Autenticación',
  'contenttypes': 'Tipos de Contenido',
  'sessions': 'Sesiones',
  'core': 'Núcleo',
  'enterprises': 'Empresas',
  'cashbox': 'Caja',
  'rooms': 'Habitaciones',
  'reservations': 'Reservas',
  'locations': 'Ubicaciones',
  'rates': 'Tarifas',
  'payments': 'Pagos',
  'notifications': 'Notificaciones',
  'otas': 'OTAs',
  'invoicing': 'Facturación',
  'calendar': 'Calendario',
  'dashboard': 'Dashboard',
  'users': 'Usuarios',
  'housekeeping': 'Limpieza',
}

/**
 * Traduce el nombre de una app (app_label) al español
 * @param {string} appLabel - Nombre de la app en inglés (ej: "core")
 * @returns {string} Nombre traducido al español (ej: "Núcleo")
 */
export const translateAppLabel = (appLabel) => {
  if (!appLabel || typeof appLabel !== 'string') {
    return appLabel
  }

  const normalized = appLabel.toLowerCase().trim()
  
  return APP_LABEL_TRANSLATIONS[normalized] || appLabel.toUpperCase()
}

/**
 * Categorías funcionales hoteleras para agrupar permisos de manera más intuitiva
 */
export const PERMISSION_CATEGORIES = {
  // Operaciones principales del hotel
  RESERVATIONS: {
    id: 'reservations',
    name: 'Reservas',
    description: 'Gestión de reservas, check-in, check-out',
    keywords: ['reservation', 'reserva', 'check-in', 'check-out', 'reservation charge', 'reservation night', 'reservation status'],
    appLabels: ['reservations'],
  },
  ROOMS: {
    id: 'rooms',
    name: 'Habitaciones',
    description: 'Gestión de habitaciones y su estado',
    keywords: ['room', 'habitación', 'room block', 'bloqueo'],
    appLabels: ['rooms', 'calendar'],
  },
  PAYMENTS: {
    id: 'payments',
    name: 'Pagos',
    description: 'Gestión de pagos, políticas y métodos de pago',
    keywords: ['payment', 'pago', 'bank transfer', 'transferencia', 'refund', 'reembolso', 'cancellation policy', 'payment policy'],
    appLabels: ['payments'],
  },
  RATES: {
    id: 'rates',
    name: 'Tarifas',
    description: 'Planes de tarifa, reglas y promociones',
    keywords: ['rate', 'tarifa', 'rate plan', 'rate rule', 'tax rule', 'promo', 'promoción'],
    appLabels: ['rates'],
  },
  INVOICING: {
    id: 'invoicing',
    name: 'Facturación',
    description: 'Facturas y comprobantes',
    keywords: ['invoice', 'factura', 'receipt', 'comprobante', 'afip'],
    appLabels: ['invoicing'],
  },
  CALENDAR: {
    id: 'calendar',
    name: 'Calendario',
    description: 'Vista de calendario y mantenimientos',
    keywords: ['calendar', 'calendario', 'maintenance', 'mantenimiento', 'event'],
    appLabels: ['calendar'],
  },
  OTAS: {
    id: 'otas',
    name: 'OTAs',
    description: 'Integración con canales de reserva',
    keywords: ['ota', 'mapping', 'mapeo', 'sync', 'imported event'],
    appLabels: ['otas'],
  },
  CONFIGURATION: {
    id: 'configuration',
    name: 'Configuración',
    description: 'Hoteles, empresas, ubicaciones y usuarios',
    keywords: ['hotel', 'enterprise', 'empresa', 'country', 'país', 'city', 'ciudad', 'state', 'provincia', 'user', 'usuario'],
    appLabels: ['core', 'enterprises', 'locations', 'users'],
  },
  ADMINISTRATION: {
    id: 'administration',
    name: 'Administración',
    description: 'Configuración del sistema y roles',
    keywords: ['group', 'grupo', 'permission', 'permiso', 'session', 'sesión', 'content type', 'log entry'],
    appLabels: ['auth', 'admin', 'contenttypes', 'sessions'],
  },
  DASHBOARD: {
    id: 'dashboard',
    name: 'Dashboard',
    description: 'Métricas y reportes',
    keywords: ['dashboard', 'métrica', 'metrics'],
    appLabels: ['dashboard'],
  },
  NOTIFICATIONS: {
    id: 'notifications',
    name: 'Notificaciones',
    description: 'Sistema de notificaciones',
    keywords: ['notification', 'notificación'],
    appLabels: ['notifications'],
  },
  HOUSEKEEPING: {
    id: 'housekeeping',
    name: 'Limpieza',
    description: 'Gestión de tareas de limpieza y mantenimiento',
    keywords: ['housekeeping', 'limpieza', 'cleaning', 'task', 'tarea', 'checklist', 'staff', 'personal'],
    appLabels: ['housekeeping'],
  },
}

/**
 * Obtiene la categoría funcional de un permiso basado en su app_label y keywords
 * @param {object} permission - Objeto de permiso
 * @returns {string} ID de la categoría o null
 */
export const getPermissionCategory = (permission) => {
  if (!permission || !permission.permission) return 'ADMINISTRATION'
  
  const appLabel = permission.permission.split('.')[0]?.toLowerCase()
  const permissionName = (permission.name || '').toLowerCase()
  const codename = (permission.codename || '').toLowerCase()
  const combined = `${permissionName} ${codename}`
  
  // Buscar categoría que coincida
  for (const [key, category] of Object.entries(PERMISSION_CATEGORIES)) {
    // Verificar app label
    if (category.appLabels.some(app => app === appLabel)) {
      return category.id
    }
    
    // Verificar keywords
    if (category.keywords.some(keyword => combined.includes(keyword.toLowerCase()))) {
      return category.id
    }
  }
  
  return 'ADMINISTRATION' // Default
}

/**
 * Permisos técnicos del sistema que no deberían aparecer en roles operativos
 * Estos son permisos internos de Django que no tienen sentido para usuarios del hotel
 * Solo deberían ser gestionados por superusuarios
 */
const TECHNICAL_PERMISSIONS_TO_HIDE = [
  // Admin - log entries
  'admin.add_logentry',
  'admin.change_logentry',
  'admin.delete_logentry',
  'admin.view_logentry',
  // Content types - técnico interno
  'contenttypes.add_contenttype',
  'contenttypes.change_contenttype',
  'contenttypes.delete_contenttype',
  'contenttypes.view_contenttype',
  // Sessions - técnico interno
  'sessions.add_session',
  'sessions.change_session',
  'sessions.delete_session',
  'sessions.view_session',
  // Auth - gestión de usuarios, grupos y permisos (solo superusuarios)
  'auth.add_permission',
  'auth.change_permission',
  'auth.delete_permission',
  'auth.view_permission',
  'auth.add_group',
  'auth.change_group',
  'auth.delete_group',
  'auth.view_group',
  'auth.add_user',
  'auth.change_user',
  'auth.delete_user',
  'auth.view_user',
]

/**
 * Verifica si un permiso es técnico y debería ocultarse
 * @param {object} permission - Objeto de permiso
 * @returns {boolean} true si debe ocultarse
 */
export const isTechnicalPermission = (permission) => {
  if (!permission || !permission.permission) return false
  return TECHNICAL_PERMISSIONS_TO_HIDE.includes(permission.permission)
}

/**
 * Filtra permisos por categoría funcional
 * @param {array} permissions - Array de permisos
 * @param {string} categoryId - ID de la categoría o 'all' para todos
 * @param {string} searchTerm - Término de búsqueda opcional
 * @param {boolean} hideTechnical - Si true, oculta permisos técnicos del sistema
 * @returns {array} Permisos filtrados
 */
export const filterPermissionsByCategory = (permissions, categoryId = 'all', searchTerm = '', hideTechnical = true) => {
  if (!Array.isArray(permissions)) return []
  
  let filtered = permissions
  
  // Filtrar permisos técnicos (por defecto)
  if (hideTechnical) {
    filtered = filtered.filter(perm => !isTechnicalPermission(perm))
  }
  
  // Filtrar por categoría
  if (categoryId !== 'all') {
    filtered = filtered.filter(perm => getPermissionCategory(perm) === categoryId)
  }
  
  // Filtrar por búsqueda
  if (searchTerm && searchTerm.trim()) {
    const term = searchTerm.toLowerCase().trim()
    filtered = filtered.filter(perm => {
      const name = translatePermissionName(perm.name || '').toLowerCase()
      const codename = (perm.codename || '').toLowerCase()
      const permission = (perm.permission || '').toLowerCase()
      const appLabel = translateAppLabel(perm.permission?.split('.')[0] || '').toLowerCase()
      
      return name.includes(term) || 
             codename.includes(term) || 
             permission.includes(term) ||
             appLabel.includes(term)
    })
  }
  
  return filtered
}

// Verbos comunes de permisos
const ACTION_TRANSLATIONS = {
  'Can add': 'Puede agregar',
  'Can change': 'Puede modificar',
  'Can delete': 'Puede eliminar',
  'Can view': 'Puede ver',
}

// Traducciones específicas de modelos y términos comunes
const MODEL_TRANSLATIONS = {
  // Modelos principales
  'Hotel': 'Hotel',
  'Room': 'Habitación',
  'Reservation': 'Reserva',
  'User': 'Usuario',
  'Group': 'Grupo',
  'Permission': 'Permiso',
  'Content Type': 'Tipo de Contenido',
  'Content type': 'Tipo de Contenido',
  'content type': 'tipo de contenido',
  
  // Ubicaciones
  'Country': 'País',
  'País': 'País',
  'State': 'Provincia',
  'Provincia/Estado': 'Provincia/Estado',
  'City': 'Ciudad',
  'Ciudad': 'Ciudad',
  
  // Otros modelos comunes
  'Enterprise': 'Empresa',
  'Empresa': 'Empresa',
  'Payment': 'Pago',
  'Invoice': 'Factura',
  'Factura': 'Factura',
  'Rate Plan': 'Plan de Tarifa',
  'Rate plan': 'Plan de Tarifa',
  'rate plan': 'plan de tarifa',
  'Tax': 'Impuesto',
  'Promotion': 'Promoción',
  'Channel': 'Canal',
  
  // Modelos especiales
  'Room Maintenance': 'Mantenimiento de Habitación',
  'Mantenimiento de Habitación': 'Mantenimiento de Habitación',
  'Calendar View': 'Vista de Calendario',
  'Vista de Calendario': 'Vista de Calendario',
  'Calendar Event': 'Evento de Calendario',
  'Evento de Calendario': 'Evento de Calendario',
  'Log Entry': 'Entrada de Log',
  'log entry': 'entrada de log',
  'Session': 'Sesión',
  'session': 'sesión',
  
  // Dashboard
  'Dashboard Metrics': 'Métrica del Dashboard',
  'Métrica del Dashboard': 'Métrica del Dashboard',
  
  // Facturación
  'Invoice Item': 'Item de Factura',
  'Item de Factura': 'Item de Factura',
  'receipt': 'comprobante',
  'AFIP Config': 'Configuración AFIP',
  'Configuración AFIP': 'Configuración AFIP',
  
  // Pagos
  'Bank Transfer Payment': 'Transferencia Bancaria',
  'Transferencia Bancaria': 'Transferencia Bancaria',
  'Cancellation Policy': 'Política de Cancelación',
  'Política de Cancelación': 'Política de Cancelación',
  'Refund': 'Reembolso',
  'Reembolso': 'Reembolso',
  'Refund Policy': 'Política de Devolución',
  'Política de Devolución': 'Política de Devolución',
  'Refund Log': 'Log de Reembolso',
  'Log de Reembolso': 'Log de Reembolso',
  'Refund Voucher': 'Voucher de Reembolso',
  'Voucher de Reembolso': 'Voucher de Reembolso',
  'Payment Gateway Config': 'Configuración de Pasarela de Pago',
  'payment gateway config': 'configuración de pasarela de pago',
  'Payment Intent': 'Intención de Pago',
  'payment intent': 'intención de pago',
  'Payment Method': 'Método de Pago',
  'payment method': 'método de pago',
  'Payment Policy': 'Política de Pago',
  'payment policy': 'política de pago',
  'Bank Reconciliation': 'Conciliación Bancaria',
  'bank reconciliation': 'conciliación bancaria',
  'Bank Reconciliation Config': 'Configuración de Conciliación Bancaria',
  'bank reconciliation config': 'configuración de conciliación bancaria',
  'Bank Reconciliation Log': 'Log de Conciliación Bancaria',
  'bank reconciliation log': 'log de conciliación bancaria',
  'Bank Transaction': 'Transacción Bancaria',
  'bank transaction': 'transacción bancaria',
  'Receipt Number Sequence': 'Secuencia de Número de Comprobante',
  'receipt number sequence': 'secuencia de número de comprobante',
  'Reconciliation Match': 'Coincidencia de Conciliación',
  'reconciliation match': 'coincidencia de conciliación',
  
  // Reservas
  'Reservation Charge': 'Cargo de Reserva',
  'reservation charge': 'cargo de reserva',
  'Reservation Night': 'Noche de Reserva',
  'reservation night': 'noche de reserva',
  'Reservation Status Change': 'Cambio de Estado de Reserva',
  'reservation status change': 'cambio de estado de reserva',
  'Reservation Change Log': 'Log de Cambios de Reserva',
  'reservation change log': 'log de cambios de reserva',
  'Room Block': 'Bloqueo de habitación',
  'Bloqueo de habitación': 'Bloqueo de habitación',
  'Channel Commission': 'Comisión de Canal',
  'channel commission': 'comisión de canal',
  
  // Tarifas
  'Rate Occupancy Price': 'Precio de Ocupación de Tarifa',
  'rate occupancy price': 'precio de ocupación de tarifa',
  'Rate Rule': 'Regla de Tarifa',
  'rate rule': 'regla de tarifa',
  'Tax Rule': 'Regla de Impuesto',
  'tax rule': 'regla de impuesto',
  'Promo Rule': 'Regla de Promoción',
  'promo rule': 'regla de promoción',
  
  // OTAs
  'OTA Config': 'Configuración OTA',
  'ota config': 'configuración OTA',
  'OTA Room Mapping': 'Mapeo de Habitación OTA',
  'ota room mapping': 'mapeo de habitación OTA',
  'OTA Room Type Mapping': 'Mapeo de Tipo de Habitación OTA',
  'ota room type mapping': 'mapeo de tipo de habitación OTA',
  'OTA Rate Plan Mapping': 'Mapeo de Plan de Tarifa OTA',
  'ota rate plan mapping': 'mapeo de plan de tarifa OTA',
  'OTA Sync Job': 'Trabajo de Sincronización OTA',
  'ota sync job': 'trabajo de sincronización OTA',
  'OTA Sync Log': 'Log de Sincronización OTA',
  'ota sync log': 'log de sincronización OTA',
  'OTA Imported Event': 'Evento Importado OTA',
  'ota imported event': 'evento importado OTA',
  
  // Notificaciones
  'notification': 'notificación',
  
  // Housekeeping
  'Housekeeping Task': 'Tarea de Limpieza',
  'Tarea de Limpieza': 'Tarea de Limpieza',
  'tarea de limpieza': 'tarea de limpieza',
  'Cleaning Staff': 'Personal de Limpieza',
  'Personal de Limpieza': 'Personal de Limpieza',
  'personal de limpieza': 'personal de limpieza',
  'Cleaning Zone': 'Zona de Limpieza',
  'Zona de Limpieza': 'Zona de Limpieza',
  'zona de limpieza': 'zona de limpieza',
  'Task Template': 'Plantilla de Tarea',
  'Plantilla de Tarea': 'Plantilla de Tarea',
  'plantilla de tarea': 'plantilla de tarea',
  'Checklist': 'Lista de Verificación',
  'Lista de Verificación': 'Lista de Verificación',
  'lista de verificación': 'lista de verificación',
  'Checklist Item': 'Item de Lista de Verificación',
  'Item de Lista de Verificación': 'Item de Lista de Verificación',
  'item de lista de verificación': 'item de lista de verificación',
  'Housekeeping Config': 'Configuración de Limpieza',
  'Configuración de Limpieza': 'Configuración de Limpieza',
  'configuración de limpieza': 'configuración de limpieza',
  
  // Términos técnicos
  'permission': 'permiso',
  'user': 'usuario',
  'group': 'grupo',
}

// Traducciones exactas (para casos especiales que no siguen el patrón estándar)
const EXACT_TRANSLATIONS = {
  // Auth & Admin
  'Can add log entry': 'Puede agregar entrada de log',
  'Can change log entry': 'Puede modificar entrada de log',
  'Can delete log entry': 'Puede eliminar entrada de log',
  'Can view log entry': 'Puede ver entrada de log',
  'Can add group': 'Puede agregar grupo',
  'Can change group': 'Puede modificar grupo',
  'Can delete group': 'Puede eliminar grupo',
  'Can view group': 'Puede ver grupo',
  'Can add permission': 'Puede agregar permiso',
  'Can change permission': 'Puede modificar permiso',
  'Can delete permission': 'Puede eliminar permiso',
  'Can view permission': 'Puede ver permiso',
  'Can add user': 'Puede agregar usuario',
  'Can change user': 'Puede modificar usuario',
  'Can delete user': 'Puede eliminar usuario',
  'Can view user': 'Puede ver usuario',
  'Can add content type': 'Puede agregar tipo de contenido',
  'Can change content type': 'Puede modificar tipo de contenido',
  'Can delete content type': 'Puede eliminar tipo de contenido',
  'Can view content type': 'Puede ver tipo de contenido',
  'Can add session': 'Puede agregar sesión',
  'Can change session': 'Puede modificar sesión',
  'Can delete session': 'Puede eliminar sesión',
  'Can view session': 'Puede ver sesión',
  
  // Core & Enterprise
  'Can add Hotel': 'Puede agregar Hotel',
  'Can change Hotel': 'Puede modificar Hotel',
  'Can delete Hotel': 'Puede eliminar Hotel',
  'Can view Hotel': 'Puede ver Hotel',
  'Can add Empresa': 'Puede agregar Empresa',
  'Can change Empresa': 'Puede modificar Empresa',
  'Can delete Empresa': 'Puede eliminar Empresa',
  'Can view Empresa': 'Puede ver Empresa',
  
  // Locations
  'Can add País': 'Puede agregar País',
  'Can change País': 'Puede modificar País',
  'Can delete País': 'Puede eliminar País',
  'Can view País': 'Puede ver País',
  'Can add Provincia/Estado': 'Puede agregar Provincia/Estado',
  'Can change Provincia/Estado': 'Puede modificar Provincia/Estado',
  'Can delete Provincia/Estado': 'Puede eliminar Provincia/Estado',
  'Can view Provincia/Estado': 'Puede ver Provincia/Estado',
  'Can add Ciudad': 'Puede agregar Ciudad',
  'Can change Ciudad': 'Puede modificar Ciudad',
  'Can delete Ciudad': 'Puede eliminar Ciudad',
  'Can view Ciudad': 'Puede ver Ciudad',
  
  // Rooms
  'Can add Habitación': 'Puede agregar Habitación',
  'Can change Habitación': 'Puede modificar Habitación',
  'Can delete Habitación': 'Puede eliminar Habitación',
  'Can view Habitación': 'Puede ver Habitación',
  
  // Reservations
  'Can add reservation': 'Puede agregar reserva',
  'Can change reservation': 'Puede modificar reserva',
  'Can delete reservation': 'Puede eliminar reserva',
  'Can view reservation': 'Puede ver reserva',
  'Can add payment': 'Puede agregar pago',
  'Can change payment': 'Puede modificar pago',
  'Can delete payment': 'Puede eliminar pago',
  'Can view payment': 'Puede ver pago',
  'Can add reservation charge': 'Puede agregar cargo de reserva',
  'Can change reservation charge': 'Puede modificar cargo de reserva',
  'Can delete reservation charge': 'Puede eliminar cargo de reserva',
  'Can view reservation charge': 'Puede ver cargo de reserva',
  'Can add reservation night': 'Puede agregar noche de reserva',
  'Can change reservation night': 'Puede modificar noche de reserva',
  'Can delete reservation night': 'Puede eliminar noche de reserva',
  'Can view reservation night': 'Puede ver noche de reserva',
  'Can add reservation status change': 'Puede agregar cambio de estado de reserva',
  'Can change reservation status change': 'Puede modificar cambio de estado de reserva',
  'Can delete reservation status change': 'Puede eliminar cambio de estado de reserva',
  'Can view reservation status change': 'Puede ver cambio de estado de reserva',
  'Can add reservation change log': 'Puede agregar log de cambios de reserva',
  'Can change reservation change log': 'Puede modificar log de cambios de reserva',
  'Can delete reservation change log': 'Puede eliminar log de cambios de reserva',
  'Can view reservation change log': 'Puede ver log de cambios de reserva',
  'Can add Bloqueo de habitación': 'Puede agregar Bloqueo de habitación',
  'Can change Bloqueo de habitación': 'Puede modificar Bloqueo de habitación',
  'Can delete Bloqueo de habitación': 'Puede eliminar Bloqueo de habitación',
  'Can view Bloqueo de habitación': 'Puede ver Bloqueo de habitación',
  'Can add channel commission': 'Puede agregar comisión de canal',
  'Can change channel commission': 'Puede modificar comisión de canal',
  'Can delete channel commission': 'Puede eliminar comisión de canal',
  'Can view channel commission': 'Puede ver comisión de canal',
  
  // Rates
  'Can add rate plan': 'Puede agregar plan de tarifa',
  'Can change rate plan': 'Puede modificar plan de tarifa',
  'Can delete rate plan': 'Puede eliminar plan de tarifa',
  'Can view rate plan': 'Puede ver plan de tarifa',
  'Can add rate rule': 'Puede agregar regla de tarifa',
  'Can change rate rule': 'Puede modificar regla de tarifa',
  'Can delete rate rule': 'Puede eliminar regla de tarifa',
  'Can view rate rule': 'Puede ver regla de tarifa',
  'Can add rate occupancy price': 'Puede agregar precio de ocupación de tarifa',
  'Can change rate occupancy price': 'Puede modificar precio de ocupación de tarifa',
  'Can delete rate occupancy price': 'Puede eliminar precio de ocupación de tarifa',
  'Can view rate occupancy price': 'Puede ver precio de ocupación de tarifa',
  'Can add tax rule': 'Puede agregar regla de impuesto',
  'Can change tax rule': 'Puede modificar regla de impuesto',
  'Can delete tax rule': 'Puede eliminar regla de impuesto',
  'Can view tax rule': 'Puede ver regla de impuesto',
  'Can add promo rule': 'Puede agregar regla de promoción',
  'Can change promo rule': 'Puede modificar regla de promoción',
  'Can delete promo rule': 'Puede eliminar regla de promoción',
  'Can view promo rule': 'Puede ver regla de promoción',
  
  // Payments
  'Can add payment gateway config': 'Puede agregar configuración de pasarela de pago',
  'Can change payment gateway config': 'Puede modificar configuración de pasarela de pago',
  'Can delete payment gateway config': 'Puede eliminar configuración de pasarela de pago',
  'Can view payment gateway config': 'Puede ver configuración de pasarela de pago',
  'Can add payment intent': 'Puede agregar intención de pago',
  'Can change payment intent': 'Puede modificar intención de pago',
  'Can delete payment intent': 'Puede eliminar intención de pago',
  'Can view payment intent': 'Puede ver intención de pago',
  'Can add payment method': 'Puede agregar método de pago',
  'Can change payment method': 'Puede modificar método de pago',
  'Can delete payment method': 'Puede eliminar método de pago',
  'Can view payment method': 'Puede ver método de pago',
  'Can add payment policy': 'Puede agregar política de pago',
  'Can change payment policy': 'Puede modificar política de pago',
  'Can delete payment policy': 'Puede eliminar política de pago',
  'Can view payment policy': 'Puede ver política de pago',
  'Can add Política de Cancelación': 'Puede agregar Política de Cancelación',
  'Can change Política de Cancelación': 'Puede modificar Política de Cancelación',
  'Can delete Política de Cancelación': 'Puede eliminar Política de Cancelación',
  'Can view Política de Cancelación': 'Puede ver Política de Cancelación',
  'Can add Reembolso': 'Puede agregar Reembolso',
  'Can change Reembolso': 'Puede modificar Reembolso',
  'Can delete Reembolso': 'Puede eliminar Reembolso',
  'Can view Reembolso': 'Puede ver Reembolso',
  'Can add Log de Reembolso': 'Puede agregar Log de Reembolso',
  'Can change Log de Reembolso': 'Puede modificar Log de Reembolso',
  'Can delete Log de Reembolso': 'Puede eliminar Log de Reembolso',
  'Can view Log de Reembolso': 'Puede ver Log de Reembolso',
  'Can add Política de Devolución': 'Puede agregar Política de Devolución',
  'Can change Política de Devolución': 'Puede modificar Política de Devolución',
  'Can delete Política de Devolución': 'Puede eliminar Política de Devolución',
  'Can view Política de Devolución': 'Puede ver Política de Devolución',
  'Can add Voucher de Reembolso': 'Puede agregar Voucher de Reembolso',
  'Can change Voucher de Reembolso': 'Puede modificar Voucher de Reembolso',
  'Can delete Voucher de Reembolso': 'Puede eliminar Voucher de Reembolso',
  'Can view Voucher de Reembolso': 'Puede ver Voucher de Reembolso',
  'Can add Transferencia Bancaria': 'Puede agregar Transferencia Bancaria',
  'Can change Transferencia Bancaria': 'Puede modificar Transferencia Bancaria',
  'Can delete Transferencia Bancaria': 'Puede eliminar Transferencia Bancaria',
  'Can view Transferencia Bancaria': 'Puede ver Transferencia Bancaria',
  'Can add bank reconciliation': 'Puede agregar conciliación bancaria',
  'Can change bank reconciliation': 'Puede modificar conciliación bancaria',
  'Can delete bank reconciliation': 'Puede eliminar conciliación bancaria',
  'Can view bank reconciliation': 'Puede ver conciliación bancaria',
  'Can add bank reconciliation config': 'Puede agregar configuración de conciliación bancaria',
  'Can change bank reconciliation config': 'Puede modificar configuración de conciliación bancaria',
  'Can delete bank reconciliation config': 'Puede eliminar configuración de conciliación bancaria',
  'Can view bank reconciliation config': 'Puede ver configuración de conciliación bancaria',
  'Can add bank reconciliation log': 'Puede agregar log de conciliación bancaria',
  'Can change bank reconciliation log': 'Puede modificar log de conciliación bancaria',
  'Can delete bank reconciliation log': 'Puede eliminar log de conciliación bancaria',
  'Can view bank reconciliation log': 'Puede ver log de conciliación bancaria',
  'Can add bank transaction': 'Puede agregar transacción bancaria',
  'Can change bank transaction': 'Puede modificar transacción bancaria',
  'Can delete bank transaction': 'Puede eliminar transacción bancaria',
  'Can view bank transaction': 'Puede ver transacción bancaria',
  'Can add receipt number sequence': 'Puede agregar secuencia de número de comprobante',
  'Can change receipt number sequence': 'Puede modificar secuencia de número de comprobante',
  'Can delete receipt number sequence': 'Puede eliminar secuencia de número de comprobante',
  'Can view receipt number sequence': 'Puede ver secuencia de número de comprobante',
  'Can add reconciliation match': 'Puede agregar coincidencia de conciliación',
  'Can change reconciliation match': 'Puede modificar coincidencia de conciliación',
  'Can delete reconciliation match': 'Puede eliminar coincidencia de conciliación',
  'Can view reconciliation match': 'Puede ver coincidencia de conciliación',
  
  // Notifications
  'Can add notification': 'Puede agregar notificación',
  'Can change notification': 'Puede modificar notificación',
  'Can delete notification': 'Puede eliminar notificación',
  'Can view notification': 'Puede ver notificación',
  
  // Housekeeping
  'Can add Tarea de Limpieza': 'Puede agregar Tarea de Limpieza',
  'Can change Tarea de Limpieza': 'Puede modificar Tarea de Limpieza',
  'Can delete Tarea de Limpieza': 'Puede eliminar Tarea de Limpieza',
  'Can view Tarea de Limpieza': 'Puede ver Tarea de Limpieza',
  'Can add Personal de Limpieza': 'Puede agregar Personal de Limpieza',
  'Can change Personal de Limpieza': 'Puede modificar Personal de Limpieza',
  'Can delete Personal de Limpieza': 'Puede eliminar Personal de Limpieza',
  'Can view Personal de Limpieza': 'Puede ver Personal de Limpieza',
  'Can add Zona de Limpieza': 'Puede agregar Zona de Limpieza',
  'Can change Zona de Limpieza': 'Puede modificar Zona de Limpieza',
  'Can delete Zona de Limpieza': 'Puede eliminar Zona de Limpieza',
  'Can view Zona de Limpieza': 'Puede ver Zona de Limpieza',
  'Can add Plantilla de Tarea': 'Puede agregar Plantilla de Tarea',
  'Can change Plantilla de Tarea': 'Puede modificar Plantilla de Tarea',
  'Can delete Plantilla de Tarea': 'Puede eliminar Plantilla de Tarea',
  'Can view Plantilla de Tarea': 'Puede ver Plantilla de Tarea',
  'Can add Lista de Verificación': 'Puede agregar Lista de Verificación',
  'Can change Lista de Verificación': 'Puede modificar Lista de Verificación',
  'Can delete Lista de Verificación': 'Puede eliminar Lista de Verificación',
  'Can view Lista de Verificación': 'Puede ver Lista de Verificación',
  'Can add Item de Lista de Verificación': 'Puede agregar Item de Lista de Verificación',
  'Can change Item de Lista de Verificación': 'Puede modificar Item de Lista de Verificación',
  'Can delete Item de Lista de Verificación': 'Puede eliminar Item de Lista de Verificación',
  'Can view Item de Lista de Verificación': 'Puede ver Item de Lista de Verificación',
  'Can add Configuración de Limpieza': 'Puede agregar Configuración de Limpieza',
  'Can change Configuración de Limpieza': 'Puede modificar Configuración de Limpieza',
  'Can delete Configuración de Limpieza': 'Puede eliminar Configuración de Limpieza',
  'Can view Configuración de Limpieza': 'Puede ver Configuración de Limpieza',
  
  // OTAs
  'Can add ota config': 'Puede agregar configuración OTA',
  'Can change ota config': 'Puede modificar configuración OTA',
  'Can delete ota config': 'Puede eliminar configuración OTA',
  'Can view ota config': 'Puede ver configuración OTA',
  'Can add ota room mapping': 'Puede agregar mapeo de habitación OTA',
  'Can change ota room mapping': 'Puede modificar mapeo de habitación OTA',
  'Can delete ota room mapping': 'Puede eliminar mapeo de habitación OTA',
  'Can view ota room mapping': 'Puede ver mapeo de habitación OTA',
  'Can add ota room type mapping': 'Puede agregar mapeo de tipo de habitación OTA',
  'Can change ota room type mapping': 'Puede modificar mapeo de tipo de habitación OTA',
  'Can delete ota room type mapping': 'Puede eliminar mapeo de tipo de habitación OTA',
  'Can view ota room type mapping': 'Puede ver mapeo de tipo de habitación OTA',
  'Can add ota rate plan mapping': 'Puede agregar mapeo de plan de tarifa OTA',
  'Can change ota rate plan mapping': 'Puede modificar mapeo de plan de tarifa OTA',
  'Can delete ota rate plan mapping': 'Puede eliminar mapeo de plan de tarifa OTA',
  'Can view ota rate plan mapping': 'Puede ver mapeo de plan de tarifa OTA',
  'Can add ota sync job': 'Puede agregar trabajo de sincronización OTA',
  'Can change ota sync job': 'Puede modificar trabajo de sincronización OTA',
  'Can delete ota sync job': 'Puede eliminar trabajo de sincronización OTA',
  'Can view ota sync job': 'Puede ver trabajo de sincronización OTA',
  'Can add ota sync log': 'Puede agregar log de sincronización OTA',
  'Can change ota sync log': 'Puede modificar log de sincronización OTA',
  'Can delete ota sync log': 'Puede eliminar log de sincronización OTA',
  'Can view ota sync log': 'Puede ver log de sincronización OTA',
  'Can add ota imported event': 'Puede agregar evento importado OTA',
  'Can change ota imported event': 'Puede modificar evento importado OTA',
  'Can delete ota imported event': 'Puede eliminar evento importado OTA',
  'Can view ota imported event': 'Puede ver evento importado OTA',
  
  // Invoicing
  'Can add Factura': 'Puede agregar Factura',
  'Can change Factura': 'Puede modificar Factura',
  'Can delete Factura': 'Puede eliminar Factura',
  'Can view Factura': 'Puede ver Factura',
  'Can add Item de Factura': 'Puede agregar Item de Factura',
  'Can change Item de Factura': 'Puede modificar Item de Factura',
  'Can delete Item de Factura': 'Puede eliminar Item de Factura',
  'Can view Item de Factura': 'Puede ver Item de Factura',
  'Can add receipt': 'Puede agregar comprobante',
  'Can change receipt': 'Puede modificar comprobante',
  'Can delete receipt': 'Puede eliminar comprobante',
  'Can view receipt': 'Puede ver comprobante',
  'Can add Configuración AFIP': 'Puede agregar Configuración AFIP',
  'Can change Configuración AFIP': 'Puede modificar Configuración AFIP',
  'Can delete Configuración AFIP': 'Puede eliminar Configuración AFIP',
  'Can view Configuración AFIP': 'Puede ver Configuración AFIP',
  
  // Calendar
  'Can add Vista de Calendario': 'Puede agregar Vista de Calendario',
  'Can change Vista de Calendario': 'Puede modificar Vista de Calendario',
  'Can delete Vista de Calendario': 'Puede eliminar Vista de Calendario',
  'Can view Vista de Calendario': 'Puede ver Vista de Calendario',
  'Can add Mantenimiento de Habitación': 'Puede agregar Mantenimiento de Habitación',
  'Can change Mantenimiento de Habitación': 'Puede modificar Mantenimiento de Habitación',
  'Can delete Mantenimiento de Habitación': 'Puede eliminar Mantenimiento de Habitación',
  'Can view Mantenimiento de Habitación': 'Puede ver Mantenimiento de Habitación',
  'Can add Evento de Calendario': 'Puede agregar Evento de Calendario',
  'Can change Evento de Calendario': 'Puede modificar Evento de Calendario',
  'Can delete Evento de Calendario': 'Puede eliminar Evento de Calendario',
  'Can view Evento de Calendario': 'Puede ver Evento de Calendario',
  
  // Dashboard
  'Can add Métrica del Dashboard': 'Puede agregar Métrica del Dashboard',
  'Can change Métrica del Dashboard': 'Puede modificar Métrica del Dashboard',
  'Can delete Métrica del Dashboard': 'Puede eliminar Métrica del Dashboard',
  'Can view Métrica del Dashboard': 'Puede ver Métrica del Dashboard',
  
  // Users
  'Can add Perfil de Usuario': 'Puede agregar Perfil de Usuario',
  'Can change Perfil de Usuario': 'Puede modificar Perfil de Usuario',
  'Can delete Perfil de Usuario': 'Puede eliminar Perfil de Usuario',
  'Can view Perfil de Usuario': 'Puede ver Perfil de Usuario',
}

/**
 * Traduce un nombre de permiso del inglés al español
 * @param {string} permissionName - Nombre del permiso en inglés (ej: "Can view Hotel")
 * @returns {string} Nombre traducido al español (ej: "Puede ver Hotel")
 */
export const translatePermissionName = (permissionName) => {
  if (!permissionName || typeof permissionName !== 'string') {
    return permissionName
  }

  // Normalizar: trim y manejar espacios múltiples
  const normalized = permissionName.trim().replace(/\s+/g, ' ')

  // Primero buscar traducción exacta
  if (EXACT_TRANSLATIONS[normalized]) {
    return EXACT_TRANSLATIONS[normalized]
  }

  // Intentar traducir usando patrones comunes
  // Patrón: "Can {action} {model}"
  let translated = normalized

  // Buscar y reemplazar verbos de acción
  for (const [enAction, esAction] of Object.entries(ACTION_TRANSLATIONS)) {
    if (normalized.startsWith(enAction)) {
      const remaining = normalized.substring(enAction.length).trim()
      
      // Buscar traducción del modelo/objeto
      let modelTranslated = remaining
      
      // Intentar traducir el modelo completo
      if (MODEL_TRANSLATIONS[remaining]) {
        modelTranslated = MODEL_TRANSLATIONS[remaining]
      } else {
        // Si no hay traducción exacta, intentar traducir palabra por palabra
        const words = remaining.split(' ')
        modelTranslated = words
          .map(word => MODEL_TRANSLATIONS[word] || word)
          .join(' ')
      }
      
      translated = `${esAction} ${modelTranslated}`
      break
    }
  }

  return translated
}

/**
 * Traduce un array de nombres de permisos
 * @param {string[]} permissionNames - Array de nombres de permisos
 * @returns {string[]} Array de nombres traducidos
 */
export const translatePermissionNames = (permissionNames) => {
  if (!Array.isArray(permissionNames)) {
    return permissionNames
  }
  return permissionNames.map(translatePermissionName)
}

/**
 * Traduce un objeto de permiso (con campo name)
 * @param {object} permission - Objeto de permiso con campo 'name'
 * @returns {object} Objeto de permiso con 'name' traducido y campo 'name_translated'
 */
export const translatePermission = (permission) => {
  if (!permission || typeof permission !== 'object') {
    return permission
  }

  const nameTranslated = translatePermissionName(permission.name)
  
  return {
    ...permission,
    name_translated: nameTranslated,
    // Mantener el original para referencia
    name_original: permission.name,
  }
}

/**
 * Traduce un array de objetos de permisos
 * @param {object[]} permissions - Array de objetos de permisos
 * @returns {object[]} Array de objetos de permisos con nombres traducidos
 */
export const translatePermissions = (permissions) => {
  if (!Array.isArray(permissions)) {
    return permissions
  }
  return permissions.map(translatePermission)
}

// Exportar diccionarios por si se necesitan extender
export { ACTION_TRANSLATIONS, MODEL_TRANSLATIONS, EXACT_TRANSLATIONS, APP_LABEL_TRANSLATIONS }

