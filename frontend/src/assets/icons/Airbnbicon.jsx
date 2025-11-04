import React from 'react'

const Airbnbicon = ({ size = '20', ...props }) => {
  return (
<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" {...props}><path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" d="M12 18.775c-1.656-2-3-3.24-3-5.275s1.503-3.5 3.003-3.5S15 11.464 15 13.5s-1.344 3.275-3 5.275m0 0c-2 2.545-5.98 2.687-7.65 1.527c-1.671-1.16-1.695-3.562-.596-6.107c1.1-2.544 2.565-5.597 5.497-9.668C10.212 3.458 10.897 3 11.997 3M12 18.775c2 2.545 5.98 2.687 7.65 1.527c1.671-1.16 1.695-3.562.596-6.107c-1.1-2.544-2.565-5.597-5.497-9.668C13.788 3.458 13.103 3 12.003 3"/></svg>
  )
}

export default Airbnbicon