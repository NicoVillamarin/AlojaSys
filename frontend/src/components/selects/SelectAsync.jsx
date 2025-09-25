import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useField } from 'formik'
import Select from 'react-select'
import LabelsContainer from 'src/components/inputs/labelsContainer'
import { useList } from 'src/hooks/useList'
import SpinnerData from 'src/components/SpinnerData'

/**
 * SelectAsync: consulta opciones desde la API usando useList(resource).
 * - Guarda en Formik el valor simple (id/clave) de la opción.
 * - props:
 *   - title, name, resource, placeholder
 *   - extraParams: filtros adicionales (hotel, etc.)
 *   - getOptionLabel/getOptionValue: mapeos (por defecto id/name)
 *   - isClearable/isSearchable, disabled
 */
const SelectAsync = ({
  title,
  name,
  resource,
  placeholder,
  disabled = false,
  isClearable = true,
  isSearchable = true,
  extraParams = {},
  getOptionLabel = (o) => o?.name ?? o?.title ?? o?.label ?? String(o?.id ?? ''),
  getOptionValue = (o) => o?.id ?? o?.value ?? '',
  onValueChange,
}) => {
  const [field, meta, helpers] = useField(name)
  const hasError = meta.touched && !!meta.error
  const [query, setQuery] = useState('')
  const didMountRef = useRef(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const { results, isPending, refetch } = useList({
    resource,
    params: { search: query, ...extraParams },
    enabled: true,
  })

  // Debounce refetch al escribir
  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const id = setTimeout(() => refetch(), 300)
    return () => clearTimeout(id)
  }, [query, refetch])

  const options = useMemo(() => results || [], [results])

  const valueOption = useMemo(() => {
    return options.find((opt) => String(getOptionValue(opt)) === String(field.value)) || null
  }, [options, field.value, getOptionValue])

  const onChange = (opt) => {
    const newValue = opt ? getOptionValue(opt) : ''
    helpers.setValue(newValue)
    if (typeof onValueChange === 'function') onValueChange(opt, newValue)
  }

  const onBlur = () => helpers.setTouched(true)

  const styles = {
    control: (base, state) => ({
      ...base,
      minHeight: 36,
      borderRadius: 6,
      borderColor: hasError ? '#f87171' : state.isFocused ? 'rgba(19,35,68,0.35)' : '#e5e7eb',
      boxShadow: state.isFocused
        ? hasError
          ? '0 0 0 2px rgba(248,113,113,0.35)'
          : '0 0 0 2px rgba(19,35,68,0.20)'
        : 'none',
      '&:hover': { borderColor: state.isFocused ? '#132344' : '#d1d5db' },
      backgroundColor: disabled ? '#f9fafb' : '#ffffff',
      cursor: disabled ? 'not-allowed' : 'default',
      fontSize: 14,
    }),
    valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
    indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
    dropdownIndicator: (base) => ({ ...base, padding: 6 }),
    clearIndicator: (base) => ({ ...base, padding: 6 }),
    menu: (base) => ({ ...base, borderRadius: 8, overflow: 'hidden', zIndex: 60 }),
    menuList: (base) => ({ ...base, paddingTop: 4, paddingBottom: 4 }),
    option: (base, state) => ({
      ...base,
      fontSize: 14,
      backgroundColor: state.isSelected ? '#132344' : state.isFocused ? '#eef2ff' : 'white',
      color: state.isSelected ? '#fff' : '#111827',
      ':active': { backgroundColor: state.isSelected ? '#132344' : '#e5e7eb' },
    }),
    placeholder: (base) => ({ ...base, color: '#6b7280' }),
  }

  return (
    <LabelsContainer title={title}>
      <div
        onMouseDown={(e) => {
          if (disabled) return
          // Abrir menú solo por interacción del usuario con el mouse
          setIsMenuOpen(true)
        }}
      >
      <Select
        inputId={name}
        name={name}
        value={valueOption}
        onChange={onChange}
        onBlur={(e) => { onBlur(e); setIsMenuOpen(false) }}
        menuIsOpen={isMenuOpen}
        onMenuClose={() => setIsMenuOpen(false)}
        openMenuOnFocus={false}
        onInputChange={(val, meta) => {
          if (meta.action === 'input-change') setQuery(val)
        }}
        options={options}
        isLoading={isPending}
        isClearable={isClearable}
        isDisabled={disabled}
        isSearchable={isSearchable}
        placeholder={placeholder}
        classNamePrefix="rs"
        styles={styles}
        getOptionLabel={getOptionLabel}
        getOptionValue={getOptionValue}
        noOptionsMessage={() => (isPending ? 'Cargando…' : 'Sin resultados')}
      />
      </div>
      {isPending && (
        <div className="mt-2">
          <SpinnerData inline size={18} label="Buscando…" />
        </div>
      )}
      {hasError && <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>}
    </LabelsContainer>
  )
}

export default SelectAsync
