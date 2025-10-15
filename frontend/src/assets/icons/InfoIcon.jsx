import React from 'react'

const InfoIcon = ({ size = '20', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 48 48" {...props    }><defs><mask id="IconifyId199e39ed35e72a3160"><g fill="none"><path fill="#555" stroke="#fff" strokeLinejoin="round" strokeWidth="4" d="M24 44a19.94 19.94 0 0 0 14.142-5.858A19.94 19.94 0 0 0 44 24a19.94 19.94 0 0 0-5.858-14.142A19.94 19.94 0 0 0 24 4A19.94 19.94 0 0 0 9.858 9.858A19.94 19.94 0 0 0 4 24a19.94 19.94 0 0 0 5.858 14.142A19.94 19.94 0 0 0 24 44Z"/><path fill="#fff" fillRule="evenodd" d="M24 11a2.5 2.5 0 1 1 0 5a2.5 2.5 0 0 1 0-5" clipRule="evenodd"/><path stroke="#fff" strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M24.5 34V20h-2M21 34h7"/></g></mask></defs><path fill="currentColor" d="M0 0h48v48H0z" mask="url(#IconifyId199e39ed35e72a3160)"/></svg>
  )
}

export default InfoIcon