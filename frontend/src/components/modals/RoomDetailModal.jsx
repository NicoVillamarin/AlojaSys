import React from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import { getStatusMeta } from 'src/utils/statusList'
import Badge from 'src/components/Badge'
import { getAmenityLabel } from 'src/utils/roomAmenities'

/**
 * RoomDetailModal: Modal para mostrar el detalle completo de una habitación
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - room: objeto habitación con toda su información
 */
const RoomDetailModal = ({ isOpen, onClose, room }) => {
  const { t } = useTranslation()

  if (!room) return null

  // Preparar imágenes para mostrar
  const allImages = []
  if (room.primary_image_url) {
    allImages.push({ url: room.primary_image_url, isPrimary: true })
  }
  if (room.images_urls && Array.isArray(room.images_urls)) {
    room.images_urls.forEach(url => {
      if (url) {
        allImages.push({ url, isPrimary: false })
      }
    })
  }

  const statusMeta = getStatusMeta(room.status, t)

  // Obtener tipo de habitación traducido
  const getRoomTypeLabel = (type) => {
    const types = {
      single: t('rooms_modal.room_types.single'),
      double: t('rooms_modal.room_types.double'),
      triple: t('rooms_modal.room_types.triple'),
      suite: t('rooms_modal.room_types.suite'),
    }
    return types[type] || type
  }

  return (
    <ModalLayout
      isOpen={isOpen}
      onClose={onClose}
      title={room.name || `Habitación #${room.number || room.id}`}
      size="lg"
      showFooter={false}
    >
      <div className="space-y-6">
        {/* Información General */}
        <div>
          <h3 className="text-lg font-semibold text-aloja-navy mb-4">
            {t('rooms_modal.detail_modal.general_info', 'Información General')}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.name')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {room.name || '-'}
              </p>
            </div>
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.number')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {room.number || '-'}
              </p>
            </div>
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.floor')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {room.floor || '-'}
              </p>
            </div>
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.type')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {getRoomTypeLabel(room.room_type)}
              </p>
            </div>
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.capacity')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {room.capacity || 0}
                {room.max_capacity && room.max_capacity > room.capacity
                  ? ` - ${room.max_capacity}`
                  : ''}
              </p>
            </div>
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.base_price')}
              </label>
              <p className="text-sm font-medium text-aloja-gray-800">
                {(room.base_currency_code || '$')} {room.base_price ? parseFloat(room.base_price).toFixed(2) : '0.00'}
              </p>
            </div>
            {(room.secondary_price != null && room.secondary_price !== '' && room.secondary_currency_code) && (
              <div>
                <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                  Tarifa secundaria
                </label>
                <p className="text-sm font-medium text-aloja-gray-800">
                  {room.secondary_currency_code} {parseFloat(room.secondary_price).toFixed(2)}
                </p>
              </div>
            )}
            <div>
              <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                {t('rooms_modal.status')}
              </label>
              <div className="mt-1">
                <Badge variant={`room-${room.status}`} size="sm">
                  {statusMeta.label}
                </Badge>
              </div>
            </div>
            {room.hotel_name && (
              <div>
                <label className="text-xs text-aloja-gray-800/70 mb-1 block">
                  {t('rooms_modal.hotel')}
                </label>
                <p className="text-sm font-medium text-aloja-gray-800">
                  {room.hotel_name}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Amenities */}
        {Array.isArray(room.amenities) && room.amenities.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-aloja-navy mb-4">
              {t('rooms_modal.amenities.title', 'Características / amenities')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {room.amenities.map((code) => (
                <span
                  key={code}
                  className="inline-flex items-center px-2.5 py-1 rounded-full bg-gray-100 text-gray-800 text-xs border border-gray-200"
                  title={code}
                >
                  {getAmenityLabel(t, code)}
                  {room?.amenities_quantities?.[code] > 1 ? ` x${room.amenities_quantities[code]}` : ''}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Descripción */}
        {room.description && (
          <div>
            <h3 className="text-lg font-semibold text-aloja-navy mb-4">
              {t('rooms_modal.description')}
            </h3>
            <p className="text-sm text-aloja-gray-800 whitespace-pre-wrap">
              {room.description}
            </p>
          </div>
        )}

        {/* Imágenes */}
        {allImages.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-aloja-navy mb-4">
              {t('rooms_modal.detail_modal.images', 'Imágenes')}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {allImages.map((image, index) => (
                <div
                  key={index}
                  className={`relative rounded-lg overflow-hidden border-2 ${
                    image.isPrimary
                      ? 'border-yellow-400 ring-2 ring-yellow-300'
                      : 'border-gray-200'
                  }`}
                >
                  <div className="aspect-square bg-gray-100">
                    <img
                      src={image.url}
                      alt={image.isPrimary ? 'Imagen principal' : `Imagen ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23ddd" width="400" height="400"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="30" dy="10.5" font-weight="bold" x="50%25" y="50%25" text-anchor="middle"%3EImagen no disponible%3C/text%3E%3C/svg%3E'
                      }}
                    />
                  </div>
                  {image.isPrimary && (
                    <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-semibold">
                      {t('rooms_modal.detail_modal.primary', 'Principal')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {allImages.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>{t('rooms_modal.detail_modal.no_images', 'No hay imágenes disponibles para esta habitación')}</p>
          </div>
        )}
      </div>
    </ModalLayout>
  )
}

export default RoomDetailModal
