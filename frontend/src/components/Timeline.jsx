import React from 'react'

/**
 * Timeline vertical tipo escalera alternando lados con tooltips al hover
 * Props:
 * - items: Array<{
 *     id: string|number,
 *     date: string|Date,         // fecha del evento
 *     title: string,             // label principal
 *     subtitle?: string,         // label secundario (opcional)
 *     color?: string,            // tailwind color classes para el nodo
 *     tooltip?: React.ReactNode, // contenido del tooltip en hover
 *   }>
 */
export default function Timeline({ items = [] }) {
  if (!items || items.length === 0) return null

  return (
    <div className="relative py-4">
      {/* Línea vertical central con gradiente */}
      <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-200 via-yellow-200 to-purple-200 transform -translate-x-1/2 rounded-full shadow-sm" />
      
      {items.map((item, index) => {
        const isLeft = index % 2 === 0
        const formatDate = (date) => {
          try {
            return new Date(date).toLocaleDateString('es-ES', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit'
            })
          } catch {
            return ''
          }
        }
        
        return (
          <div key={item.id} className="group relative flex items-center justify-center mb-3 min-h-[60px]">
            {/* Línea curva conectora desde el nodo hasta la tarjeta */}
            <svg 
              className="absolute top-1/2 -translate-y-1/2 pointer-events-none z-0"
              style={{
                left: isLeft ? '0' : '50%',
                width: '50%',
                height: '40px',
              }}
              preserveAspectRatio="none"
            >
              <path
                d={isLeft 
                  ? `M ${100}% 20 Q ${75}% 20, ${50}% 20` 
                  : `M 0 20 Q ${25}% 20, ${50}% 20`
                }
                stroke="currentColor"
                strokeWidth="2"
                fill="none"
                className="text-gray-300 group-hover:text-aloja-navy/40 transition-colors duration-200"
                strokeDasharray="4 4"
              />
            </svg>

            {/* Contenido del evento - escalado pero con espacio al círculo */}
            <div
              className={`
                absolute ${isLeft ? 'left-0 right-[57%]' : 'right-0 left-[57%]'} 
                flex ${isLeft ? 'justify-end' : 'justify-start'}
              `}
            >
              <div
                className={`
                  relative bg-gradient-to-br from-white to-gray-50 rounded-xl shadow-md border-2 border-gray-100 p-3 z-10
                  hover:shadow-xl hover:border-aloja-navy/30 hover:scale-[1.02] transition-all duration-200
                  max-w-[280px]
                `}
              >
                {/* Flecha blanca apuntando al círculo */}
                <div 
                  className={`
                    absolute top-1/2 -translate-y-1/2 w-0 h-0 
                    border-t-[10px] border-b-[10px] border-transparent
                    ${isLeft 
                      ? 'right-[-10px] border-l-[10px] border-l-white' 
                      : 'left-[-10px] border-r-[10px] border-r-white'
                    }
                  `}
                  style={{
                    filter: 'drop-shadow(1px 0 1px rgba(0, 0, 0, 0.1))'
                  }}
                />
                
                <div className="text-sm font-semibold text-aloja-navy mb-1">
                  {item.title}
                </div>
                
                <div className="text-xs text-gray-500">
                  {formatDate(item.date)}
                </div>
                
                {item.subtitle && (
                  <div className="text-xs text-gray-600 mt-1">
                    {item.subtitle}
                  </div>
                )}
              </div>
            </div>
            
            {/* Nodo central limpio */}
            <div 
              className={`
                absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20
              `}
            >
              {/* Anillo exterior centrado, solo visible en hover */}
              <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full ${item.color || 'bg-aloja-navy'} opacity-0 group-hover:opacity-20 group-hover:scale-150 transition-all duration-500`} />
              
              {/* Nodo principal limpio sin sombra */}
              <div 
                className={`
                  w-5 h-5 rounded-full ring-[3px] ring-white
                  ${item.color || 'bg-aloja-navy'}
                  group-hover:scale-110 transition-transform duration-200
                `}
              />
            </div>
            
            {/* Tooltip detallado en hover */}
            {item.tooltip && (
              <div 
                className={`
                  pointer-events-none absolute top-full mt-2 opacity-0 
                  group-hover:opacity-100 group-hover:pointer-events-auto 
                  transition-opacity duration-200 z-30
                  ${isLeft ? 'left-0' : 'right-0'}
                `}
              >
                <div className="w-80 bg-white shadow-2xl ring-1 ring-black/10 rounded-xl p-4 text-sm text-aloja-gray-800">
                  {item.tooltip}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
