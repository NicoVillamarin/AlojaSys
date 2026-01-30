import { Formik } from 'formik'
import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import SelectBasic from 'src/components/selects/SelectBasic'
import SelectAsync from 'src/components/selects/SelectAsync'
import FileImageMultiple from 'src/components/inputs/FileImageMultiple'
import LabelsContainer from 'src/components/inputs/LabelsContainer'
import { ROOM_AMENITIES, ROOM_AMENITY_CATEGORIES, getAmenityLabel } from 'src/utils/roomAmenities'
import * as Yup from 'yup'

const isQuantifiableAmenity = (code) => {
  const found = ROOM_AMENITIES.find((a) => a.code === code)
  return found?.categoryKey === 'beds'
}


/**
 * RoomsModal: crear/editar habitaci?n
 * Props:
 * - isOpen: boolean
 * - onClose: () => void
 * - isEdit?: boolean
 * - room?: objeto habitaci?n existente (para editar)
 * - onSuccess?: (data) => void (se llama al crear/editar OK)
 */
const RoomsModal = ({ isOpen, onClose, isEdit = false, room, onSuccess }) => {
  const { t } = useTranslation()
  const [amenitySearch, setAmenitySearch] = useState('')
  const [customAmenity, setCustomAmenity] = useState('')
  
  // Funci?n para convertir archivo a base64
  const convertFileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => resolve(reader.result)
      reader.onerror = error => reject(error)
    })
  }

  const { mutate: createRoom, isPending: creating } = useCreate({
    resource: 'rooms',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  const { mutate: updateRoom, isPending: updating } = useUpdate({
    resource: 'rooms',
    onSuccess: (data) => {
      onSuccess && onSuccess(data)
      onClose && onClose()
    },
  })

  // Preparar im?genes existentes para edici?n
  const existingImages = []
  if (isEdit && room) {
    // Agregar imagen principal si existe
    if (room.primary_image_url) {
      existingImages.push(room.primary_image_url)
    }
    // Agregar im?genes adicionales si existen
    if (room.images_urls && Array.isArray(room.images_urls)) {
      existingImages.push(...room.images_urls)
    }
  }

  const initialValues = {
    hotel: room?.hotel ?? '',
    hotel_name: room?.hotel_name ?? '',
    base_currency: room?.base_currency ?? '',
    base_currency_code: room?.base_currency_code ?? '',
    name: room?.name ?? '',
    number: room?.number ?? '',
    floor: room?.floor ?? '',
    room_type: room?.room_type ?? '',
    capacity: room?.capacity ?? '',
    max_capacity: room?.max_capacity ?? '',
    base_price: room?.base_price != null ? String(room.base_price) : '0',
    secondary_price: room?.secondary_price != null ? String(room.secondary_price) : '',
    secondary_currency: room?.secondary_currency ?? '',
    // Solo lectura: el precio OTA se gestiona en Smoobu (channel manager) y se publica a OTAs.
    // No lo enviamos en el payload de creaci?n/edici?n de habitaci?n.
    ota_price: room?.ota_price != null ? String(room.ota_price) : '',
    status: room?.status ?? 'available',
    description: room?.description ?? '',
    amenities: Array.isArray(room?.amenities) ? room.amenities : [],
    amenities_quantities: room?.amenities_quantities && typeof room.amenities_quantities === 'object' ? room.amenities_quantities : {},
    images: [], // Array de archivos de im?genes nuevas
    imagesToDelete: [], // ?ndices de im?genes existentes a eliminar
    primaryImageIndex: null, // ?ndice de la imagen principal si se cambi?
  }

  const validationSchema = Yup.object().shape({
    hotel: Yup.string().required(t('rooms_modal.hotel_required')),
    name: Yup.string().required(t('rooms_modal.name_required')),
    number: Yup.string().required(t('rooms_modal.number_required')),
    floor: Yup.string().required(t('rooms_modal.floor_required')),
    room_type: Yup.string().required(t('rooms_modal.type_required')),
    capacity: Yup.number()
    .transform((v, o) => (o === '' ? undefined : v))
    .typeError(t('rooms_modal.capacity_number'))
    .integer(t('rooms_modal.capacity_integer'))
    .min(1, t('rooms_modal.capacity_min'))
    .required(t('rooms_modal.capacity_required')),
    max_capacity: Yup.number()
    .transform((v, o) => (o === '' ? undefined : v))
    .typeError(t('rooms_modal.max_capacity_number'))
    .integer(t('rooms_modal.max_capacity_integer'))
    .min(1, t('rooms_modal.max_capacity_min'))
    .required(t('rooms_modal.max_capacity_required')),
    base_price: Yup.number()
    .transform((val, original) => (original === '' ? undefined : val))
    .typeError(t('rooms_modal.base_price_number'))
    .moreThan(0, t('rooms_modal.base_price_more_than'))
    .required(t('rooms_modal.base_price_required')),
    base_currency: Yup.mixed().required('La moneda de la tarifa principal es requerida'),
    secondary_price: Yup.number()
      .transform((val, original) => (original === '' ? null : val))
      .nullable()
      .typeError('La tarifa secundaria debe ser un número'),
    secondary_currency: Yup.mixed().nullable(),
    status: Yup.string().required(t('rooms_modal.status_required')),
  }).test('secondary_tariff_pair', 'Tarifa secundaria inválida', function (values) {
    const price = values?.secondary_price
    const currency = values?.secondary_currency
    const hasPrice = price !== null && price !== undefined
    const hasCurrency = currency !== null && currency !== undefined && String(currency) !== ''

    if (hasPrice && Number(price) <= 0) {
      return this.createError({ path: 'secondary_price', message: 'La tarifa secundaria debe ser mayor a 0' })
    }

    if (hasPrice !== hasCurrency) {
      // Si hay precio sin moneda, marcar moneda. Si hay moneda sin precio, marcar precio.
      return this.createError({
        path: hasPrice ? 'secondary_currency' : 'secondary_price',
        message: 'Completá precio y moneda de la tarifa secundaria (o dejá ambos vacíos).',
      })
    }
    return true
  })

  const [instanceKey, setInstanceKey] = useState(0)
  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  useEffect(() => {
    if (isOpen) {
      setAmenitySearch('')
      setCustomAmenity('')
    }
  }, [isOpen])

  return (
    <Formik
      key={isEdit ? `edit-${room?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={async (values) => {
        try {
          const payload = {
            hotel: values.hotel ? Number(values.hotel) : undefined,
            name: values.name || undefined,
            number: values.number !== '' ? Number(values.number) : undefined,
            floor: values.floor !== '' ? Number(values.floor) : undefined,
            room_type: values.room_type || undefined,
            capacity: values.capacity ? Number(values.capacity) : undefined,
            max_capacity: values.max_capacity ? Number(values.max_capacity) : undefined,
            base_price: values.base_price ? Number(values.base_price) : undefined,
            base_currency: values.base_currency !== '' ? Number(values.base_currency) : null,
            secondary_price: values.secondary_price !== '' ? Number(values.secondary_price) : null,
            secondary_currency: values.secondary_currency !== '' ? Number(values.secondary_currency) : null,
            status: values.status || undefined,
            description: values.description || undefined,
            amenities: Array.isArray(values.amenities) ? values.amenities : undefined,
            amenities_quantities: values.amenities_quantities && typeof values.amenities_quantities === 'object' ? values.amenities_quantities : undefined,
          }

          // Procesar im?genes
          const images = values.images || []
          if (images.length > 0) {
            // Separar imagen principal (primera con isPrimary o primera del array)
            const primaryImage = images.find(img => img.isPrimary) || images[0]
            const additionalImages = images.filter((img, idx) => 
              idx !== images.indexOf(primaryImage)
            )

            // Convertir imagen principal a base64
            if (primaryImage && primaryImage.file) {
              const primaryBase64 = await convertFileToBase64(primaryImage.file)
              payload.primary_image_base64 = primaryBase64
              payload.primary_image_filename = primaryImage.file.name
            }

            // Convertir im?genes adicionales a base64
            if (additionalImages.length > 0) {
              const imagesBase64 = []
              for (const img of additionalImages) {
                if (img.file) {
                  const imgBase64 = await convertFileToBase64(img.file)
                  imagesBase64.push({
                    base64: imgBase64,
                    filename: img.file.name
                  })
                }
              }
              if (imagesBase64.length > 0) {
                payload.images_base64 = imagesBase64
              }
            }
          }

          // En modo edici?n, agregar informaci?n de eliminaci?n y cambio de principal
          if (isEdit && room?.id) {
            if (values.imagesToDelete && values.imagesToDelete.length > 0) {
              payload.images_to_delete = values.imagesToDelete
            }
            if (values.primaryImageIndex !== null && values.primaryImageIndex !== undefined) {
              // Si se cambi? la imagen principal, necesitamos reorganizar
              // Esto se manejar? en el backend
            }
          }

          if (isEdit && room?.id) {
            updateRoom({ id: room.id, body: payload })
          } else {
            createRoom(payload)
          }
        } catch (error) {
          console.error('? Error procesando im?genes:', error)
          // En caso de error, enviar sin im?genes
          const payload = {
            hotel: values.hotel ? Number(values.hotel) : undefined,
            name: values.name || undefined,
            number: values.number !== '' ? Number(values.number) : undefined,
            floor: values.floor !== '' ? Number(values.floor) : undefined,
            room_type: values.room_type || undefined,
            capacity: values.capacity ? Number(values.capacity) : undefined,
            max_capacity: values.max_capacity ? Number(values.max_capacity) : undefined,
            base_price: values.base_price ? Number(values.base_price) : undefined,
            base_currency: values.base_currency !== '' ? Number(values.base_currency) : null,
            secondary_price: values.secondary_price !== '' ? Number(values.secondary_price) : null,
            secondary_currency: values.secondary_currency !== '' ? Number(values.secondary_currency) : null,
            status: values.status || undefined,
            description: values.description || undefined,
            amenities: Array.isArray(values.amenities) ? values.amenities : undefined,
          }
          if (isEdit && room?.id) {
            updateRoom({ id: room.id, body: payload })
          } else {
            createRoom(payload)
          }
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('rooms_modal.edit_room') : t('rooms_modal.create_room')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('rooms_modal.save_changes') : t('rooms_modal.create')}
          cancelText={t('rooms_modal.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='xl'
        >
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
            <SelectAsync
              title={`${t('rooms_modal.hotel')} *`}
              name='hotel'
              resource='hotels'
              placeholder={t('rooms_modal.hotel_placeholder')}
              getOptionLabel={(h) => h?.name}
              getOptionValue={(h) => h?.id}
            />
            <InputText title={`${t('rooms_modal.name')} *`} name='name' placeholder={t('rooms_modal.name_placeholder')} />
            <InputText title={`${t('rooms_modal.number')} *`} name='number' placeholder={t('rooms_modal.number_placeholder')} />
            <InputText title={`${t('rooms_modal.floor')} *`} name='floor' placeholder={t('rooms_modal.floor_placeholder')} />
            <SelectBasic
              title={`${t('rooms_modal.type')} *`}
              name='room_type'
              placeholder={t('rooms_modal.type_placeholder')}
              options={[
                { value: 'single', label: t('rooms_modal.room_types.single') },
                { value: 'double', label: t('rooms_modal.room_types.double') },
                { value: 'triple', label: t('rooms_modal.room_types.triple') },
                { value: 'suite', label: t('rooms_modal.room_types.suite') },
              ]}
            />
            <InputText title={`${t('rooms_modal.capacity')} *`} name='capacity' placeholder={t('rooms_modal.capacity_placeholder')} />
            <InputText title={`${t('rooms_modal.max_capacity')} *`} name='max_capacity' placeholder={t('rooms_modal.max_capacity_placeholder')} />
            <div className='lg:col-span-2'>
              <div className='rounded-lg border border-gray-200 p-4 bg-white'>
                <div className='text-xs font-semibold text-aloja-gray-800/70 uppercase tracking-wide mb-3'>
                  Tarifa principal
                </div>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <InputText
                      title={`${t('rooms_modal.base_price')} *`}
                      name='base_price'
                      placeholder={t('rooms_modal.base_price_placeholder')}
                    />
                  </div>
                  <div>
                    <SelectAsync
                      title='Moneda'
                      name='base_currency'
                      resource='currencies'
                      placeholder='Seleccioná moneda'
                      getOptionLabel={(c) => (c?.name ? `${c.code} - ${c.name}` : c?.code)}
                      getOptionValue={(c) => c?.id}
                      isClearable={false}
                      onValueChange={(opt) => setFieldValue('base_currency_code', opt?.code || '')}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className='lg:col-span-2'>
              <div className='rounded-lg border border-gray-200 p-4 bg-white'>
                <div className='text-xs font-semibold text-aloja-gray-800/70 uppercase tracking-wide mb-3'>
                  Tarifa secundaria (opcional)
                </div>
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <InputText title='Precio secundario' name='secondary_price' placeholder='85.00' />
                  <SelectAsync
                    title='Moneda secundaria'
                    name='secondary_currency'
                    resource='currencies'
                    placeholder='Seleccioná moneda'
                    getOptionLabel={(c) => (c?.name ? `${c.code} - ${c.name}` : c?.code)}
                    getOptionValue={(c) => c?.id}
                    isClearable
                  />
                </div>
                <div className='text-xs text-gray-500 mt-2'>
                  Se guarda como referencia (monto + moneda) y no afecta el cálculo de tarifas actual.
                </div>
              </div>
            </div>
            <InputText
              title={t('rooms_modal.ota_price')}
              name='ota_price'
              placeholder={t('rooms_modal.ota_price_placeholder')}
              disabled
              inputClassName='bg-gray-100 text-gray-500 cursor-not-allowed'
              statusMessage={t('rooms_modal.ota_price_help')}
              statusType='info'
            />
            <SelectBasic
              title={`${t('rooms_modal.status')} *`}
              name='status'
              options={[
                { value: 'available', label: t('rooms_modal.statuses.available') },
                { value: 'occupied', label: t('rooms_modal.statuses.occupied') },
                { value: 'maintenance', label: t('rooms_modal.statuses.maintenance') },
                { value: 'out_of_service', label: t('rooms_modal.statuses.out_of_service') },
                { value: 'reserved', label: t('rooms_modal.statuses.reserved') },
              ]}
            />
            <div className='lg:col-span-2'>
              <InputTextTarea title={t('rooms_modal.description')} name='description' placeholder={t('rooms_modal.description_placeholder')} rows={3} />
            </div>
            <div className='lg:col-span-2'>
              <LabelsContainer title={t('rooms_modal.amenities.title', 'Características / amenities')}>
                <div className='rounded-lg border border-gray-200 p-4 space-y-3 bg-white'>
                  {/* Buscador */}
                  <div className='flex flex-col gap-2 md:flex-row md:items-center md:justify-between'>
                    <div className='w-full md:w-2/3'>
                      <input
                        type='text'
                        value={amenitySearch}
                        onChange={(e) => setAmenitySearch(e.target.value)}
                        placeholder={t('rooms_modal.amenities.search_placeholder', 'Buscar…')}
                        className='w-full border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm transition-all'
                      />
                    </div>
                    <div className='w-full md:w-1/3 flex gap-2'>
                      <input
                        type='text'
                        value={customAmenity}
                        onChange={(e) => setCustomAmenity(e.target.value)}
                        placeholder={t('rooms_modal.amenities.add_custom_placeholder', 'Agregar etiqueta…')}
                        className='flex-1 border border-gray-200 focus:border-aloja-navy/50 focus:ring-2 focus:ring-aloja-navy/20 rounded-lg px-3 py-2 text-sm transition-all'
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            const raw = (customAmenity || '').trim()
                            if (!raw) return
                            const code = `custom:${raw}`
                            const current = Array.isArray(values.amenities) ? values.amenities : []
                            const exists = current.some((c) => String(c).toLowerCase() === code.toLowerCase())
                            if (!exists) setFieldValue('amenities', [...current, code])
                            setCustomAmenity('')
                          }
                        }}
                      />
                      <button
                        type='button'
                        className='px-3 py-2 rounded-lg bg-aloja-navy text-white text-sm hover:opacity-90'
                        onClick={() => {
                          const raw = (customAmenity || '').trim()
                          if (!raw) return
                          const code = `custom:${raw}`
                          const current = Array.isArray(values.amenities) ? values.amenities : []
                          const exists = current.some((c) => String(c).toLowerCase() === code.toLowerCase())
                          if (!exists) setFieldValue('amenities', [...current, code])
                          setCustomAmenity('')
                        }}
                        disabled={!customAmenity.trim()}
                        title={t('rooms_modal.amenities.add_custom_btn', 'Agregar')}
                      >
                        {t('rooms_modal.amenities.add_custom_btn', 'Agregar')}
                      </button>
                    </div>
                  </div>

                  {/* Chips seleccionados */}
                  {Array.isArray(values.amenities) && values.amenities.length > 0 && (
                    <div className='flex flex-wrap gap-2'>
                      {values.amenities.map((code) => (
                        <span
                          key={code}
                          className='inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-gray-100 text-gray-800 text-xs border border-gray-200'
                          title={code}
                        >
                          <span className='font-medium'>
                            {getAmenityLabel(t, code)}
                            {isQuantifiableAmenity(code) && values?.amenities_quantities?.[code] > 1 ? ` x${values.amenities_quantities[code]}` : ''}
                          </span>
                          <button
                            type='button'
                            className='text-gray-500 hover:text-gray-800'
                            onClick={() => {
                              const next = values.amenities.filter((c) => c !== code)
                              setFieldValue('amenities', next)
                              if (values?.amenities_quantities?.[code] != null) {
                                const nextQ = { ...(values.amenities_quantities || {}) }
                                delete nextQ[code]
                                setFieldValue('amenities_quantities', nextQ)
                              }
                            }}
                            aria-label={t('rooms_modal.amenities.remove', 'Quitar')}
                          >
                            ✕
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Lista de checks por categorías */}
                  <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                    {ROOM_AMENITY_CATEGORIES.map((cat) => {
                      const q = (amenitySearch || '').trim().toLowerCase()
                      const items = ROOM_AMENITIES
                        .filter((a) => a.categoryKey === cat.key)
                        .filter((a) => {
                          if (!q) return true
                          const label = (t(a.i18nKey) || '').toLowerCase()
                          return label.includes(q) || a.code.includes(q)
                        })

                      if (items.length === 0) return null

                      return (
                        <div key={cat.key} className='space-y-2'>
                          <div className='text-xs font-semibold text-aloja-gray-800/70 uppercase tracking-wide'>
                            {t(cat.i18nKey)}
                          </div>
                          <div className='space-y-2'>
                            {items.map((a) => {
                              const checked = Array.isArray(values.amenities) && values.amenities.includes(a.code)
                              return (
                                <div key={a.code} className='flex items-center justify-between gap-3'>
                                  <label className='flex items-center gap-2 text-sm text-gray-800'>
                                    <input
                                      type='checkbox'
                                      checked={checked}
                                      onChange={() => {
                                        const current = Array.isArray(values.amenities) ? values.amenities : []
                                        const isOn = current.includes(a.code)
                                        if (isOn) {
                                          setFieldValue('amenities', current.filter((c) => c !== a.code))
                                          if (values?.amenities_quantities?.[a.code] != null) {
                                            const nextQ = { ...(values.amenities_quantities || {}) }
                                            delete nextQ[a.code]
                                            setFieldValue('amenities_quantities', nextQ)
                                          }
                                        } else {
                                          setFieldValue('amenities', [...current, a.code])
                                          if (isQuantifiableAmenity(a.code)) {
                                            const nextQ = { ...(values.amenities_quantities || {}) }
                                            if (!nextQ[a.code]) nextQ[a.code] = 1
                                            setFieldValue('amenities_quantities', nextQ)
                                          }
                                        }
                                      }}
                                    />
                                    <span>{t(a.i18nKey)}</span>
                                  </label>

                                  {checked && isQuantifiableAmenity(a.code) ? (
                                    <div className='flex items-center gap-2'>
                                      <span className='text-xs text-gray-500'>x</span>
                                      <input
                                        type='number'
                                        min='1'
                                        value={values?.amenities_quantities?.[a.code] ?? 1}
                                        onChange={(e) => {
                                          const raw = Number(e.target.value)
                                          const qty = Number.isFinite(raw) && raw >= 1 ? Math.floor(raw) : 1
                                          const nextQ = { ...(values.amenities_quantities || {}) }
                                          nextQ[a.code] = qty
                                          setFieldValue('amenities_quantities', nextQ)
                                        }}
                                        className='w-16 border border-gray-200 rounded-md px-2 py-1 text-sm'
                                        aria-label={`Cantidad de ${t(a.i18nKey)}`}
                                      />
                                    </div>
                                  ) : null}
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  <div className='text-xs text-gray-500'>
                    {t(
                      'rooms_modal.amenities.help',
                      'Estas características se guardan en la habitación y luego podés mostrarlas en el detalle o en tu web externa.'
                    )}
                  </div>
                </div>
              </LabelsContainer>
            </div>
            <div className='lg:col-span-2'>
              <FileImageMultiple
                name='images'
                label={t('rooms_modal.images') || 'Im?genes de la habitaci?n'}
                compress={true}
                maxWidth={1920}
                maxHeight={1080}
                quality={0.9}
                maxSize={5 * 1024 * 1024} // 5MB
                maxImages={10}
                existingImages={existingImages}
                className='mt-4'
              />
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default RoomsModal