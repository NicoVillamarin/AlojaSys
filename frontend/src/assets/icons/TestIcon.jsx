import React from 'react'

const TestIcon = ({ size = '20', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 48 48" {...props}><defs><mask id="IconifyId19a117a0e8021009a0"><g fill="none" stroke="#fff" strokeWidth="4"><path strokeLinecap="round" d="M12 4h24"/><path strokeLinecap="round" strokeLinejoin="round" d="m10.777 30l7.242-14.961V4h12.01v11.039L37.245 30"/><path fill="#555" strokeLinejoin="round" d="M7.794 43.673a3.273 3.273 0 0 1-1.52-4.372L10.777 30S18 35 24 30s13.246 0 13.246 0l4.49 9.305A3.273 3.273 0 0 1 38.787 44H9.22c-.494 0-.981-.112-1.426-.327Z"/></g></mask></defs><path fill="currentColor" d="M0 0h48v48H0z" mask="url(#IconifyId19a117a0e8021009a0)"/></svg>
  )
}

export default TestIcon