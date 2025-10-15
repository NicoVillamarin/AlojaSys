import React from 'react'

const EyeSlashIcon = ({ size = '24', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" {...props}><path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m15 18l-.722-3.25M2 8a10.645 10.645 0 0 0 20 0m-2 7l-1.726-2.05M4 15l1.726-2.05M9 18l.722-3.25"/></svg>
  )
}

export default EyeSlashIcon