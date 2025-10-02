import React from 'react'
import Select from 'react-select'
import LabelsContainer from '../inputs/LabelsContainer'

/**
 * Select standalone (sin Formik) con estilos consistentes del sistema.
 * Útil para filtros, búsquedas y cualquier select que no esté en un formulario Formik.
 * 
 * @example
 * // Uso básico
 * <SelectStandalone
 *   title="Hotel"
 *   value={selectedHotel}
 *   onChange={setSelectedHotel}
 *   options={hotels}
 *   getOptionLabel={(h) => h.name}
 *   getOptionValue={(h) => h.id}
 * />
 * 
 * @example
 * // Con auto-selección y deshabilitar
 * <SelectStandalone
 *   title="Hotel"
 *   subtitle={hasSingleHotel ? "(autoseleccionado)" : ""}
 *   value={selectedHotel}
 *   onChange={setSelectedHotel}
 *   options={hotels}
 *   isDisabled={hasSingleHotel}
 *   isClearable={!hasSingleHotel}
 * />
 */
const SelectStandalone = ({
  title = '',
  subtitle = '',
  value,
  onChange,
  options = [],
  placeholder = 'Seleccionar...',
  isDisabled = false,
  isClearable = true,
  isSearchable = true,
  isMulti = false,
  getOptionLabel = (o) => o?.label ?? o?.name ?? String(o ?? ''),
  getOptionValue = (o) => o?.value ?? o?.id ?? String(o ?? ''),
  error,
  className = '',
  zIndex = 9999,
  ...props
}) => {
  const styles = {
    control: (base, state) => ({
      ...base,
      minHeight: 36,
      borderRadius: 6,
      borderColor: error ? '#f87171' : state.isFocused ? 'rgba(19,35,68,0.35)' : '#e5e7eb',
      boxShadow: state.isFocused
        ? error
          ? '0 0 0 2px rgba(248,113,113,0.35)'
          : '0 0 0 2px rgba(19,35,68,0.20)'
        : 'none',
      '&:hover': { 
        borderColor: state.isFocused ? '#132344' : '#d1d5db' 
      },
      backgroundColor: state.isDisabled ? '#f9fafb' : '#ffffff',
      cursor: state.isDisabled ? 'not-allowed' : 'pointer',
      pointerEvents: state.isDisabled ? 'auto' : 'auto',
      fontSize: 14,
    }),
    valueContainer: (base) => ({ ...base, padding: '2px 8px' }),
    indicatorsContainer: (base) => ({ ...base, paddingRight: 6 }),
    dropdownIndicator: (base) => ({ ...base, padding: 6 }),
    clearIndicator: (base) => ({ ...base, padding: 6 }),
    menu: (base) => ({ 
      ...base, 
      borderRadius: 8, 
      overflow: 'hidden', 
      zIndex: zIndex 
    }),
    menuList: (base) => ({ ...base, paddingTop: 4, paddingBottom: 4 }),
    option: (base, state) => ({
      ...base,
      fontSize: 14,
      backgroundColor: state.isSelected 
        ? '#132344' 
        : state.isFocused 
          ? '#eef2ff' 
          : 'white',
      color: state.isSelected ? '#fff' : '#111827',
      ':active': { 
        backgroundColor: state.isSelected ? '#132344' : '#e5e7eb' 
      },
    }),
    placeholder: (base) => ({ ...base, color: '#6b7280' }),
    multiValue: (base) => ({
      ...base,
      backgroundColor: '#e0e7ff',
    }),
    multiValueLabel: (base) => ({
      ...base,
      color: '#3730a3',
    }),
    multiValueRemove: (base) => ({
      ...base,
      color: '#3730a3',
      ':hover': {
        backgroundColor: '#c7d2fe',
        color: '#1e1b4b',
      },
    }),
  }

  return (
    <div className={className}>
      <LabelsContainer title={title}>
        <div className={isDisabled ? 'cursor-not-allowed' : ''}>
          <Select
            value={value}
            onChange={onChange}
            options={options}
            placeholder={placeholder}
            isClearable={isClearable}
            isDisabled={isDisabled}
            isSearchable={isSearchable}
            isMulti={isMulti}
            classNamePrefix="rs"
            styles={styles}
            getOptionLabel={getOptionLabel}
            getOptionValue={getOptionValue}
            noOptionsMessage={() => 'Sin resultados'}
            {...props}
          />
        </div>
        {error && <div className="text-xs text-red-600 mt-0.5">{error}</div>}
      </LabelsContainer>
    </div>
  )
}

export default SelectStandalone

