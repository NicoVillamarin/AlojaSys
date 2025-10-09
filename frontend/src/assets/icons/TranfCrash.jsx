import React from 'react'

const TranfCrash = ({ size = '20', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 48 48" {...props}><g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3"><path d="M3.398 40.21c.246 2.495 2.258 4.288 4.763 4.425C11.382 44.812 16.562 45 24 45s12.618-.188 15.84-.365c2.504-.137 4.516-1.93 4.762-4.425c.212-2.149.398-5.183.398-9.21s-.186-7.061-.398-9.21c-.246-2.495-2.258-4.288-4.763-4.425C36.618 17.188 31.438 17 24 17s-12.618.188-15.84.365c-2.504.137-4.516 1.93-4.762 4.425C3.186 23.94 3 26.973 3 31s.186 7.061.398 9.21M24 9V3m8 9V6m-16 6V6"/><path d="M28 26.286S26.4 25 24 25c-2 0-4 1.286-4 3c0 4.286 8 1.714 8 6c0 1.714-2 3-4 3c-2.4 0-4-1.286-4-1.286M24 25v-2m0 16v-2m13-6h-1m-25 0h1"/></g></svg>
  )
}

export default TranfCrash