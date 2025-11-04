import React from 'react'

const ChannelsIcon = ({ size = '20', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" {...props}><g fill="none" stroke="currentColor" strokeWidth="1.5"><rect width="7" height="5" rx=".6" transform="matrix(0 -1 -1 0 22 21)"/><rect width="7" height="5" rx=".6" transform="matrix(0 -1 -1 0 7 15.5)"/><rect width="7" height="5" rx=".6" transform="matrix(0 -1 -1 0 22 10)"/><path d="M17 17.5h-3.5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2H17M11.5 12H7"/></g></svg>
  )
}

export default ChannelsIcon