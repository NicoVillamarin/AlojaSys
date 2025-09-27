import React from 'react'

const CheckinIcon = ({ size = '20', ...props }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M3 12h12" />
      <path d="M11 8l4 4-4 4" />
      <path d="M21 5v14" />
    </svg>
  )
}

export default CheckinIcon


