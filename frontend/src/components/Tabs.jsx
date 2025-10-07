import React from 'react'

const Tabs = ({ tabs, activeTab, onTabChange, className = '' }) => {
  return (
    <div className={`border-b border-gray-200 ${className}`}>
      <div className="overflow-x-auto">
        <nav className="flex space-x-4 sm:space-x-8" style={{ minWidth: 'max-content' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => onTabChange(tab.id)}
              className={`py-3 sm:py-4 px-2 sm:px-1 border-b-2 font-medium text-sm transition-colors duration-200 whitespace-nowrap flex-shrink-0 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              style={{ minWidth: 'fit-content' }}
            >
              <div className="flex items-center space-x-1 sm:space-x-2">
                {tab.icon && (
                  <span className={`text-sm sm:text-base ${
                    activeTab === tab.id ? 'text-blue-500' : 'text-gray-400'
                  }`}>
                    {tab.icon}
                  </span>
                )}
                <span className="text-xs sm:text-sm">{tab.label}</span>
              </div>
            </button>
          ))}
        </nav>
      </div>
    </div>
  )
}

export default Tabs