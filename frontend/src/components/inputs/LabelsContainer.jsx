import React from 'react'

const LabelsContainer = ({ children, title }) => {
  return (
    <div className='flex flex-col gap-1'>
        <label className='text-xs text-aloja-gray-800/70'>{title}</label>
        {children}
    </div>
  )
}

export default LabelsContainer