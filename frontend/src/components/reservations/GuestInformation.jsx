import React from 'react'
import { useFormikContext } from 'formik'
import InputText from 'src/components/inputs/InputText'
import PeopleIcon from 'src/assets/icons/PeopleIcon'

const GuestInformation = () => {
  const { values, setFieldValue, errors, touched } = useFormikContext()
  
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
            Huésped Principal
          </h3>
        </div>
        
        {/* Información Personal */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
            Información Personal
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputText
              title="Nombre completo *"
              name="guest_name"
              placeholder="Ej: Juan Pérez"
              value={values.guest_name || ''}
              onChange={(e) => setFieldValue('guest_name', e.target.value)}
              error={touched.guest_name && errors.guest_name}
            />
            <InputText
              title="Documento *"
              name="guest_document"
              placeholder="DNI, Pasaporte, etc."
              value={values.guest_document || ''}
              onChange={(e) => setFieldValue('guest_document', e.target.value)}
              error={touched.guest_document && errors.guest_document}
            />
          </div>
        </div>

        {/* Información de Contacto */}
        <div className="border-t border-blue-200 pt-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
            Información de Contacto
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputText
              title="Email *"
              name="guest_email"
              type="email"
              placeholder="juan@email.com"
              value={values.guest_email || ''}
              onChange={(e) => setFieldValue('guest_email', e.target.value)}
              error={touched.guest_email && errors.guest_email}
            />
            <InputText
              title="Teléfono *"
              name="guest_phone"
              placeholder="+54 9 11 1234-5678"
              value={values.guest_phone || ''}
              onChange={(e) => setFieldValue('guest_phone', e.target.value)}
              error={touched.guest_phone && errors.guest_phone}
            />
            <div className="md:col-span-2">
              <InputText
                title="Dirección de contacto *"
                name="contact_address"
                placeholder="Calle 123, Ciudad, País"
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
              <h3 className="text-lg font-bold text-red-900">Capacidad Excedida</h3>
              <p className="text-red-700">
                Has seleccionado {requestedGuests} huéspedes, pero la habitación "{values.room_data.name}" 
                tiene una capacidad máxima de {maxCapacity} huéspedes. Solo se mostrarán {maxCapacity} huéspedes.
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
              Otros Huéspedes ({otherGuestsCount})
            </h3>
          </div>

          <div className="space-y-6">
            {values.other_guests?.map((guest, index) => (
              <div key={index} className="bg-white p-6 rounded-lg border border-green-200 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3 mb-6">
                  <h4 className="text-lg font-semibold text-gray-800">Huésped {index + 2}</h4>
                </div>
                
                {/* Información Personal */}
                <div className="mb-6">
                  <h5 className="text-sm font-semibold text-gray-700 mb-4 uppercase tracking-wide">
                    Información Personal
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Nombre completo *
                      </label>
                      <input
                        type="text"
                        value={guest.name || ''}
                        onChange={(e) => updateGuest(index, 'name', e.target.value)}
                        placeholder="Ej: María García"
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
                        Documento *
                      </label>
                      <input
                        type="text"
                        value={guest.document || ''}
                        onChange={(e) => updateGuest(index, 'document', e.target.value)}
                        placeholder="DNI, Pasaporte, etc."
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
                    Información de Contacto
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email *
                      </label>
                      <input
                        type="email"
                        value={guest.email || ''}
                        onChange={(e) => updateGuest(index, 'email', e.target.value)}
                        placeholder="maria@email.com"
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
                        Teléfono *
                      </label>
                      <input
                        type="text"
                        value={guest.phone || ''}
                        onChange={(e) => updateGuest(index, 'phone', e.target.value)}
                        placeholder="+54 9 11 1234-5678"
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
                        Dirección de contacto *
                      </label>
                      <input
                        type="text"
                        value={guest.address || ''}
                        onChange={(e) => updateGuest(index, 'address', e.target.value)}
                        placeholder="Calle 123, Ciudad, País"
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
          <h3 className="text-xl font-bold text-gray-900">Resumen de Huéspedes</h3>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-gray-800">
                Total de huéspedes: <span className={requestedGuests > maxCapacity ? "text-red-600" : "text-blue-600"}>{totalGuests}</span>
                {values.room_data && (
                  <span className="text-sm text-gray-500 ml-2">
                    / {maxCapacity} máximo
                  </span>
                )}
                {requestedGuests > maxCapacity && (
                  <span className="text-sm text-red-500 ml-2">
                    (solicitados: {requestedGuests})
                  </span>
                )}
              </p>
              {totalGuests > 1 && (
                <p className="text-sm text-gray-600 mt-1">
                  1 principal + {otherGuestsCount} {otherGuestsCount === 1 ? 'huésped' : 'huéspedes'}
                </p>
              )}
              {values.room_data && (
                <p className="text-xs text-gray-500 mt-1">
                  Habitación: {values.room_data.name} ({values.room_data.room_type})
                </p>
              )}
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${requestedGuests > maxCapacity ? "text-red-600" : "text-blue-600"}`}>
                {totalGuests}
              </div>
              <div className="text-xs text-gray-500 uppercase tracking-wide">Huéspedes</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GuestInformation