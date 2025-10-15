import React from 'react'

const ToggleButton = ({ 
  isOpen, 
  onToggle, 
  openLabel, 
  closedLabel, 
  icon: Icon,
  closedIcon: ClosedIcon,
  className = ""
}) => {
  return (
    <button
      onClick={onToggle}
      className={`inline-flex items-center gap-2 px-3 py-2 bg-white rounded-xl shadow hover:shadow-md transition-all duration-200 group ${className}`}
    >
      <div className="p-1 rounded-md bg-aloja-navy/10 group-hover:bg-aloja-navy/20 transition-colors">
        <div className={`transition-all duration-300 ${isOpen ? 'rotate-0' : 'rotate-180'}`}>
          {isOpen ? (Icon && <Icon className="w-4 h-4" />) : (ClosedIcon && <ClosedIcon className="w-4 h-4" />)}
        </div>
      </div>
      <span className="text-sm font-medium text-aloja-gray-800">
        {isOpen ? openLabel : closedLabel}
      </span>
    </button>
  )
}

export default ToggleButton
