import React from 'react'
import { useFormikContext } from 'formik'
import { useTranslation } from 'react-i18next'
import InputText from 'src/components/inputs/InputText'
import InputDocument from 'src/components/inputs/InputDocument'
import PeopleIcon from 'src/assets/icons/PeopleIcon'

const GuestInformation = () => {
  const { t } = useTranslation()
  const { values, setFieldValue, errors, touched } = useFormikContext()

  const isBookingProxyEmail = (email) => {
    const e = String(email || '').trim().toLowerCase()
    return e.endsWith('@guest.booking.com')
  }
  
  const requestedGuests = values.guests || 1
  const maxCapacity = values.room_data?.max_capacity || 10
  const totalGuests = Math.min(requestedGuests, maxCapacity)
  const otherGuestsCount = Math.max(0, totalGuests - 1)
  
  // Inicializar otros huéspedes si no existen
  React.useEffect(() => {
    if (otherGuestsCount > 0) {
      const currentOtherGuests = values.other_guests || []
      if (currentOtherGuests.length !== otherGuestsCount) {
        const newOtherGuests = Array.from({ length: otherGuestsCount }, (_, index) => 
          currentOtherGuests[index] || { 
            name: '', 
            document: '', 
            email: '', 
            phone: '', 
            address: '' 
          }
        )
        setFieldValue('other_guests', newOtherGuests)
      }
    } else if (values.other_guests && values.other_guests.length > 0) {
      setFieldValue('other_guests', [])
    }
  }, [totalGuests, setFieldValue])

  const updateGuest = (index, field, value) => {
    const newGuests = [...(values.other_guests || [])]
    newGuests[index] = { ...newGuests[index], [field]: value }
    setFieldValue('other_guests', newGuests)
  }

  return (
    <div className="space-y-8">
      {/* Huésped Principal */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-200 shadow-sm">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-blue-100 rounded-lg">
            <PeopleIcon className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-xl font-bold text-blue-900">
            {t('guest_information.primary_guest')}
          </h3>
        </div>
        
        {/* Información Personal */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
            {t('guest_information.personal_info')}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputText
              title={`${t('guest_information.full_name')} *`}
              name="guest_name"
              placeholder={t('guest_information.full_name_placeholder')}
              value={values.guest_name || ''}
              onChange={(e) => setFieldValue('guest_name', e.target.value)}
              error={touched.guest_name && errors.guest_name}
            />
            <InputDocument
              title={`${t('guest_information.document')} *`}
              name="guest_document"
              placeholder={t('guest_information.document_placeholder')}
              inputClassName="w-full"
            />
          </div>
        </div>

        {/* Información de Contacto */}
        <div className="border-t border-blue-200 pt-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
            {t('guest_information.contact_info')}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputText
              title={`${t('guest_information.email')} *`}
              name="guest_email"
              type="email"
              placeholder={t('guest_information.email_placeholder')}
              value={values.guest_email || ''}
              onChange={(e) => setFieldValue('guest_email', e.target.value)}
              error={touched.guest_email && errors.guest_email}
                statusMessage={
                  isBookingProxyEmail(values.guest_email)
                    ? t('guest_information.booking_proxy_email_help')
                    : undefined
                }
                statusType={isBookingProxyEmail(values.guest_email) ? 'warning' : 'info'}
            />
            <InputText
              title={`${t('guest_information.phone')} *`}
              name="guest_phone"
              placeholder={t('guest_information.phone_placeholder')}
              value={values.guest_phone || ''}
              onChange={(e) => setFieldValue('guest_phone', e.target.value)}
              error={touched.guest_phone && errors.guest_phone}
            />
            <div className="md:col-span-2">
              <InputText
                title={`${t('guest_information.contact_address')} *`}
                name="contact_address"
                placeholder={t('guest_information.contact_address_placeholder')}
                value={values.contact_address || ''}
                onChange={(e) => setFieldValue('contact_address', e.target.value)}
                error={touched.contact_address && errors.contact_address}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Advertencia de Capacidad */}
      {values.room_data && requestedGuests > maxCapacity && (
        <div className="bg-gradient-to-br from-red-50 to-orange-50 p-4 rounded-xl border border-red-200 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-red-900">{t('guest_information.capacity_exceeded')}</h3>
              <p className="text-red-700">
                {t('guest_information.capacity_exceeded_msg', { 
                  requested: requestedGuests, 
                  room_name: values.room_data.name, 
                  max: maxCapacity 
                })}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Otros Huéspedes */}
      {otherGuestsCount > 0 && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-xl border border-green-200 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <PeopleIcon className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-green-900">
              {t('guest_information.other_guests_count', { count: otherGuestsCount })}
            </h3>
          </div>

          <div className="space-y-6">
            {values.other_guests?.map((guest, index) => (
              <div key={index} className="bg-white p-6 rounded-lg border border-green-200 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3 mb-6">
                  <h4 className="text-lg font-semibold text-gray-800">{t('guest_information.guest_number', { number: index + 2 })}</h4>
                </div>
                
                {/* Información Personal */}
                <div className="mb-6">
                  <h5 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
                    {t('guest_information.personal_info')}
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('guest_information.full_name')} *
                      </label>
                      <input
                        type="text"
                        value={guest.name || ''}
                        onChange={(e) => updateGuest(index, 'name', e.target.value)}
                        placeholder={t('guest_information.full_name_placeholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errors.other_guests?.[index]?.name ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.other_guests?.[index]?.name && (
                        <p className="mt-1 text-sm text-red-600">{errors.other_guests[index].name}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('guest_information.document')} *
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="\d*"
                        maxLength={15}
                        value={guest.document || ''}
                        onChange={(e) => {
                          const sanitized = (e.target.value || '').replace(/\D+/g, '').slice(0, 15)
                          updateGuest(index, 'document', sanitized)
                        }}
                        placeholder={t('guest_information.document_placeholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errors.other_guests?.[index]?.document ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.other_guests?.[index]?.document && (
                        <p className="mt-1 text-sm text-red-600">{errors.other_guests[index].document}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Información de Contacto */}
                <div className="border-t border-gray-200 pt-6">
                  <h5 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
                    {t('guest_information.contact_info')}
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('guest_information.email')} *
                      </label>
                      <input
                        type="email"
                        value={guest.email || ''}
                        onChange={(e) => updateGuest(index, 'email', e.target.value)}
                        placeholder={t('guest_information.email_placeholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errors.other_guests?.[index]?.email ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.other_guests?.[index]?.email && (
                        <p className="mt-1 text-sm text-red-600">{errors.other_guests[index].email}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('guest_information.phone')} *
                      </label>
                      <input
                        type="text"
                        value={guest.phone || ''}
                        onChange={(e) => updateGuest(index, 'phone', e.target.value)}
                        placeholder={t('guest_information.phone_placeholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errors.other_guests?.[index]?.phone ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.other_guests?.[index]?.phone && (
                        <p className="mt-1 text-sm text-red-600">{errors.other_guests[index].phone}</p>
                      )}
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        {t('guest_information.contact_address')} *
                      </label>
                      <input
                        type="text"
                        value={guest.address || ''}
                        onChange={(e) => updateGuest(index, 'address', e.target.value)}
                        placeholder={t('guest_information.contact_address_placeholder')}
                        className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                          errors.other_guests?.[index]?.address ? 'border-red-500' : 'border-gray-300'
                        }`}
                      />
                      {errors.other_guests?.[index]?.address && (
                        <p className="mt-1 text-sm text-red-600">{errors.other_guests[index].address}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Resumen de Huéspedes */}
      <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-6 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-gray-100 rounded-lg">
            <PeopleIcon className="w-6 h-6 text-gray-600" />
          </div>
          <h3 className="text-xl font-bold text-gray-900">{t('guest_information.guests_summary')}</h3>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-gray-800">
                {t('guest_information.total_guests')} <span className={requestedGuests > maxCapacity ? "text-red-600" : "text-blue-600"}>{totalGuests}</span>
                {values.room_data && (
                  <span className="text-sm text-gray-500 ml-2">
                    / {maxCapacity} {t('guest_information.max_capacity')}
                  </span>
                )}
                {requestedGuests > maxCapacity && (
                  <span className="text-sm text-red-500 ml-2">
                    ({t('guest_information.requested')} {requestedGuests})
                  </span>
                )}
              </p>
              {totalGuests > 1 && (
                <p className="text-sm text-gray-600 mt-1">
                  {t('guest_information.principal_plus', { 
                    count: otherGuestsCount, 
                    plural: otherGuestsCount === 1 ? t('guest_information.guest') : t('guest_information.guests') 
                  })}
                </p>
              )}
              {values.room_data && (
                <p className="text-xs text-gray-500 mt-1">
                  {t('guest_information.room_info', { 
                    name: values.room_data.name, 
                    type: values.room_data.room_type 
                  })}
                </p>
              )}
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${requestedGuests > maxCapacity ? "text-red-600" : "text-blue-600"}`}>
                {totalGuests}
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-wide">{t('guest_information.guests')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GuestInformation