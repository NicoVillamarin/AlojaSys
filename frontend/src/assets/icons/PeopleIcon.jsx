import React from 'react'

const PeopleIcon = ({size = '1em', ...props}) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" {...props}><g fill="none" stroke="currentColor" strokeWidth="2"><circle cx="7" cy="6" r="3"/><path strokeLinecap="round" strokeLinejoin="round" d="M10 13H5.818a3 3 0 0 0-2.964 2.537L2.36 18.69A2 2 0 0 0 4.337 21H9m12.64-2.309l-.494-3.154A3 3 0 0 0 18.182 13h-2.364a3 3 0 0 0-2.964 2.537l-.493 3.154A2 2 0 0 0 14.337 21h5.326a2 2 0 0 0 1.976-2.309"/><circle cx="17" cy="6" r="3"/></g></svg>
  )
}

export default PeopleIcon