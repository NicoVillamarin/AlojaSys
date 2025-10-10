import React from 'react'

const Checkbox = ({ 
  label, 
  checked, 
  onChange, 
  disabled = false,
  className = '',
  helpText,
  ...props 
}) => {
  return (
    <div className={`space-y-1 ${className}`}>
      <label className="flex items-center">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange && onChange(e.target.checked)}
          disabled={disabled}
          className={`rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 ${
            disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
          }`}
          {...props}
        />
        <span className={`ml-2 text-sm ${disabled ? 'text-gray-400' : 'text-gray-700'}`}>
          {label}
        </span>
      </label>
      {helpText && (
        <p className="text-xs text-gray-500 ml-6">{helpText}</p>
      )}
    </div>
  )
}

export default Checkbox
