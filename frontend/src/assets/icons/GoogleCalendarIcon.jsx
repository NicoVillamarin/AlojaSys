import React from 'react'

const GoogleCalendarIcon = ({ size = '20', ...props }) => {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" {...props}><g fill="none" stroke="currentColor" strokeLinejoin="round"><path d="m13.055 10.25l2-1.5v6.5m-7.11-5.393c.2-.489.41-1.107 1.61-1.107s1.5 1 1.5 1.5s-.5 1.5-2 1.5c1.5 0 2 1 2 1.5s-.3 1.5-1.5 1.5s-1.41-.618-1.61-1.107"/><path strokeLinecap="round" d="M22.5 2.5v3h-17v17h-3a1 1 0 0 1-1-1v-19a1 1 0 0 1 1-1h19a1 1 0 0 1 1 1"/><path strokeLinecap="round" d="M1.5 18h21L18 22.5H5.5"/><path strokeLinecap="round" d="M18 22.5v-17h4.5V18"/></g></svg>
  )
}

export default GoogleCalendarIcon