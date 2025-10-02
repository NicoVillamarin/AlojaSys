import React from 'react'
import { useField } from 'formik'
import Select from 'react-select'
import LabelsContainer from 'src/components/inputs/LabelsContainer'

/**
 * Select básico con react-select + Formik.
 * Guarda en Formik el valor simple (no el objeto opción).
 */
const SelectBasic = ({
  title,
  name,
  options = [],
  placeholder,
  disabled = false,
  className = '',
  selectClassName = '',
  isClearable = false,
  isSearchable = false,
  getOptionLabel = (o) => (o && o.label != null ? o.label : String(o ?? '')),
  getOptionValue = (o) => (o && o.value != null ? o.value : String(o ?? '')),
  ...props
}) => {
  const [field, meta, helpers] = useField(name)
  const hasError = meta.touched && !!meta.error

  const valueOption = React.useMemo(() => {
    return options.find((opt) => String(getOptionValue(opt)) === String(field.value)) || null
  }, [options, field.value, getOptionValue])

  const onChange = (opt) => {
    helpers.setValue(opt ? getOptionValue(opt) : '')
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
      <Select
        inputId={name}
        name={name}
        value={valueOption}
        onChange={onChange}
        onBlur={onBlur}
        options={options}
        isClearable={isClearable}
        isDisabled={disabled}
        isSearchable={isSearchable}
        placeholder={placeholder}
        className={className}
        classNamePrefix="rs"
        styles={styles}
        getOptionLabel={getOptionLabel}
        getOptionValue={getOptionValue}
        {...props}
      />
      {hasError && <div className="text-xs text-red-600 mt-0.5">{meta.error}</div>}
    </LabelsContainer>
  )
}

export default SelectBasic