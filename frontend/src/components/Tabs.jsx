import React from 'react'

const Tabs = ({ tabs, activeTab, onTabChange, className = '' }) => {
  return (
    <div className={`border-b border-gray-200 ${className}`}>
      <nav className="flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              {tab.icon && (
                <span className={`text-base ${
                  activeTab === tab.id ? 'text-blue-500' : 'text-gray-400'
                }`}>
                  {tab.icon}
                </span>
              )}
              <span>{tab.label}</span>
            </div>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default Tabs