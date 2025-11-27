import React, { useEffect, useState } from 'react'
import { Formik } from 'formik'
import * as Yup from 'yup'
import { useTranslation } from 'react-i18next'
import ModalLayout from 'src/layouts/ModalLayout'
import InputText from 'src/components/inputs/InputText'
import InputTextTarea from 'src/components/inputs/InputTextTarea'
import SelectAsync from 'src/components/selects/SelectAsync'
import SelectBasic from 'src/components/selects/SelectBasic'
import { useCreate } from 'src/hooks/useCreate'
import { useUpdate } from 'src/hooks/useUpdate'
import { useUserHotels } from 'src/hooks/useUserHotels'
import { useList } from 'src/hooks/useList'
import Button from 'src/components/Button'
import XIcon from 'src/assets/icons/Xicon'

const validationSchema = (t) => Yup.object().shape({
  hotel: Yup.number().required(t('housekeeping.checklists.validations.hotel_required')),
  name: Yup.string().required(t('housekeeping.checklists.validations.name_required')),
})

const ChecklistModal = ({ isOpen, onClose, isEdit = false, checklist, onSuccess }) => {
  const { t } = useTranslation()
  const { hasSingleHotel, singleHotelId } = useUserHotels()
  const [instanceKey, setInstanceKey] = useState(0)

  const initialValues = {
    hotel: checklist?.hotel ?? (hasSingleHotel ? singleHotelId : ''),
    name: checklist?.name ?? '',
    description: checklist?.description ?? '',
    room_type: checklist?.room_type ?? '',
    task_type: checklist?.task_type ?? '',
    is_default: checklist?.is_default ?? false,
    items: checklist?.items?.map((item, idx) => ({
      id: item.id,
      name: item.name,
      description: item.description || '',
      order: item.order ?? idx,
      is_required: item.is_required ?? true,
      temp_id: `temp_${Date.now()}_${idx}`,
    })) || [],
  }

  const { mutate: createItem } = useCreate({
    resource: 'housekeeping/checklist-items',
    onSuccess: () => {}, // Silencioso, no mostrar toast por cada item
  })
  const { mutate: updateItem } = useUpdate({
    resource: 'housekeeping/checklist-items',
    onSuccess: () => {}, // Silencioso
  })

  const createItemsForChecklist = async (checklistId, items) => {
    const newItems = items.filter(item => !item.id && item.name?.trim())
    if (newItems.length === 0) return

    // Crear items secuencialmente para evitar problemas de concurrencia
    for (const item of newItems) {
      createItem({
        body: {
          checklist: checklistId,
          name: item.name.trim(),
          description: item.description?.trim() || '',
          order: item.order || 0,
          is_required: item.is_required !== undefined ? item.is_required : true,
        }
      })
      // Pequeña pausa entre creaciones
      await new Promise(resolve => setTimeout(resolve, 150))
    }
  }

  const syncChecklistItems = async (checklistId, currentItems, existingItems) => {
    const existingIds = existingItems.map(i => i.id).filter(Boolean)
    
    // Crear items nuevos
    const toCreate = currentItems.filter(item => !item.id && item.name?.trim())
    if (toCreate.length > 0) {
      await createItemsForChecklist(checklistId, toCreate)
    }
    
    // Actualizar items existentes
    const toUpdate = currentItems.filter(item => {
      if (!item.id || !existingIds.includes(item.id)) return false
      const existing = existingItems.find(ei => ei.id === item.id)
      return existing && (
        existing.name !== item.name || 
        existing.order !== item.order ||
        existing.is_required !== item.is_required
      )
    })
    
    for (const item of toUpdate) {
      updateItem({
        id: item.id,
        body: {
          name: item.name.trim(),
          description: item.description?.trim() || '',
          order: item.order || 0,
          is_required: item.is_required !== undefined ? item.is_required : true,
        }
      })
      await new Promise(resolve => setTimeout(resolve, 150))
    }
  }

  const { mutate: createChecklist, isPending: creating } = useCreate({
    resource: 'housekeeping/checklists',
    onSuccess: (data) => {
      // Crear items después de crear el checklist
      if (data.id && itemsToSave.length > 0) {
        createItemsForChecklist(data.id, itemsToSave).finally(() => {
          onSuccess && onSuccess(data)
        })
      } else {
        onSuccess && onSuccess(data)
      }
    },
  })
  const { mutate: updateChecklist, isPending: updating } = useUpdate({
    resource: 'housekeeping/checklists',
    onSuccess: (data) => {
      // Sincronizar items después de actualizar
      if (data.id && itemsToSave.length > 0) {
        syncChecklistItems(data.id, itemsToSave, checklist?.items || []).finally(() => {
          onSuccess && onSuccess(data)
        })
      } else {
        onSuccess && onSuccess(data)
      }
    },
  })

  useEffect(() => {
    if (isOpen && !isEdit) {
      setInstanceKey((k) => k + 1)
    }
  }, [isOpen, isEdit])

  return (
    <Formik
      key={isEdit ? `edit-${checklist?.id ?? 'new'}` : `create-${instanceKey}`}
      enableReinitialize
      initialValues={initialValues}
      validationSchema={validationSchema(t)}
      onSubmit={async (values) => {
        const payload = {
          hotel: values.hotel || undefined,
          name: values.name || undefined,
          description: values.description || undefined,
          room_type: values.room_type || undefined,
          task_type: values.task_type || undefined,
          is_default: values.is_default !== undefined ? values.is_default : false,
        }
        // Guardar items para usarlos en onSuccess
        setItemsToSave(values.items || [])
        if (isEdit && checklist?.id) {
          updateChecklist({ id: checklist.id, body: payload })
        } else {
          createChecklist(payload)
        }
      }}
    >
      {({ values, handleChange, handleSubmit, setFieldValue, errors, touched }) => (
        <ModalLayout
          isOpen={isOpen}
          onClose={onClose}
          title={isEdit ? t('housekeeping.checklists.modal.edit_title') : t('housekeeping.checklists.modal.create_title')}
          onSubmit={handleSubmit}
          submitText={isEdit ? t('common.save') : t('common.create')}
          cancelText={t('common.cancel')}
          submitDisabled={creating || updating}
          submitLoading={creating || updating}
          size='xl'
        >
          <div className='space-y-5'>
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5'>
              <SelectAsync
                title={`${t('common.hotel')} *`}
                name='hotel'
                resource='hotels'
                placeholder={t('common.select_placeholder')}
                getOptionLabel={(h) => h?.name}
                getOptionValue={(h) => h?.id}
              />
              <InputText
                title={`${t('housekeeping.checklists.name')} *`}
                name='name'
                placeholder={t('housekeeping.checklists.name_placeholder')}
              />
              <SelectBasic
                title={t('housekeeping.checklists.room_type')}
                name='room_type'
                options={[
                  { value: '', label: t('common.all') },
                  { value: 'single', label: t('rooms_modal.room_types.single') },
                  { value: 'double', label: t('rooms_modal.room_types.double') },
                  { value: 'triple', label: t('rooms_modal.room_types.triple') },
                  { value: 'suite', label: t('rooms_modal.room_types.suite') },
                ]}
                placeholder={t('common.select_placeholder')}
                isClearable
              />
              <SelectBasic
                title={t('housekeeping.task_type')}
                name='task_type'
                options={[
                  { value: '', label: t('common.all') },
                  { value: 'daily', label: t('housekeeping.types.daily') },
                  { value: 'checkout', label: t('housekeeping.types.checkout') },
                  { value: 'maintenance', label: t('housekeeping.types.maintenance') },
                ]}
                placeholder={t('common.select_placeholder')}
                isClearable
              />
              <div className='lg:col-span-2'>
                <InputTextTarea
                  title={t('housekeeping.checklists.description')}
                  name='description'
                  placeholder={t('housekeeping.checklists.description_placeholder')}
                />
              </div>
              <div className='lg:col-span-2'>
                <label htmlFor='is_default' className='flex items-center gap-2 cursor-pointer'>
                  <input
                    id='is_default'
                    name='is_default'
                    type='checkbox'
                    className='rounded border-gray-300'
                    checked={!!values.is_default}
                    onChange={(e) => setFieldValue('is_default', e.target.checked)}
                  />
                  <span className='text-sm text-aloja-gray-800/80'>{t('housekeeping.checklists.is_default')}</span>
                </label>
              </div>
            </div>

            {/* Items del Checklist */}
            <div className='border-t pt-4'>
              <div className='flex items-center justify-between mb-3'>
                <h3 className='text-sm font-medium text-aloja-gray-800'>{t('housekeeping.checklists.items')}</h3>
                <Button
                  variant='secondary'
                  size='sm'
                  onClick={() => {
                    const newItem = {
                      name: '',
                      description: '',
                      order: values.items.length,
                      is_required: true,
                      temp_id: `temp_${Date.now()}`,
                    }
                    setFieldValue('items', [...values.items, newItem])
                  }}
                >
                  {t('housekeeping.checklists.add_item')}
                </Button>
              </div>
              <div className='space-y-3'>
                {values.items.map((item, index) => (
                  <div key={item.temp_id || item.id} className='p-3 border border-gray-200 rounded-lg bg-gray-50'>
                    <div className='grid grid-cols-1 lg:grid-cols-12 gap-3 items-start'>
                      <div className='lg:col-span-1'>
                        <InputText
                          title={t('housekeeping.checklists.item_order')}
                          name={`items[${index}].order`}
                          type='number'
                          placeholder='0'
                        />
                      </div>
                      <div className='lg:col-span-5'>
                        <InputText
                          title={t('housekeeping.checklists.item_name')}
                          name={`items[${index}].name`}
                          placeholder={t('housekeeping.checklists.item_name_placeholder')}
                        />
                      </div>
                      <div className='lg:col-span-5'>
                        <InputText
                          title={t('housekeeping.checklists.item_description')}
                          name={`items[${index}].description`}
                          placeholder={t('housekeeping.checklists.item_description_placeholder')}
                        />
                      </div>
                      <div className='lg:col-span-1 flex items-end'>
                        <button
                          type='button'
                          onClick={() => {
                            const newItems = values.items.filter((_, i) => i !== index)
                            setFieldValue('items', newItems)
                          }}
                          className='p-2 text-red-600 hover:bg-red-50 rounded'
                        >
                          <XIcon size="20" />
                        </button>
                      </div>
                      <div className='lg:col-span-12'>
                        <label className='flex items-center gap-2 cursor-pointer'>
                          <input
                            type='checkbox'
                            checked={!!item.is_required}
                            onChange={(e) => {
                              const newItems = [...values.items]
                              newItems[index].is_required = e.target.checked
                              setFieldValue('items', newItems)
                            }}
                            className='rounded border-gray-300'
                          />
                          <span className='text-xs text-aloja-gray-800/80'>{t('housekeeping.checklists.item_is_required')}</span>
                        </label>
                      </div>
                    </div>
                  </div>
                ))}
                {values.items.length === 0 && (
                  <p className='text-sm text-gray-500 text-center py-4'>{t('housekeeping.checklists.no_items')}</p>
                )}
              </div>
            </div>
          </div>
        </ModalLayout>
      )}
    </Formik>
  )
}

export default ChecklistModal

