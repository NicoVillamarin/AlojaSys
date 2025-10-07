import React, { useEffect, useRef, useState } from 'react';
import 'animate.css';

const LoadingScreen = ({ onComplete }) => {
  const progressRef = useRef(0);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [showDocument, setShowDocument] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [showWhiteScreen, setShowWhiteScreen] = useState(false);

  const reservationSteps = [
    "Generando reserva...",
    "Validando datos...",
    "Confirmando disponibilidad...",
    "Procesando pago...",
    "Finalizando reserva..."
  ];

  useEffect(() => {
    // Fade in suave al inicio
    const fadeInTimer = setTimeout(() => {
      setIsVisible(true);
    }, 100);

    // Simular progreso de carga con pasos de reserva
    const loadingInterval = setInterval(() => {
      progressRef.current += Math.random() * 12;
      if (progressRef.current >= 100) {
        progressRef.current = 100;
        setProgress(100);
        setCurrentStep(4);
        setShowDocument(true);
        clearInterval(loadingInterval);
        
        console.log('Progreso llegó al 100%, iniciando secuencia de transición...');
        
        // Agregar delay de 2 segundos adicionales después de llegar al 100%
        setTimeout(() => {
          console.log('Iniciando transición a pantalla blanca...');
          
          // Primero fade out de la pantalla de carga
          setIsFadingOut(true);
          
          // Después de 1.5 segundos, mostrar pantalla blanca
          setTimeout(() => {
            setShowWhiteScreen(true);
            console.log('Mostrando pantalla blanca...');
            
            // Después de 1 segundo en pantalla blanca, ir al login
            setTimeout(() => {
              console.log('Yendo al login...');
              onComplete();
            }, 1000);
          }, 1500);
        }, 2000); // 2 segundos de espera después del 100%
      } else {
        setProgress(progressRef.current);
        // Cambiar paso basado en progreso
        const stepIndex = Math.floor((progressRef.current / 100) * reservationSteps.length);
        setCurrentStep(Math.min(stepIndex, reservationSteps.length - 1));
        
        // Mostrar documento cuando llegue al 50%
        if (progressRef.current > 50 && !showDocument) {
          setShowDocument(true);
        }
      }
    }, 150);

    return () => {
      clearInterval(loadingInterval);
      clearTimeout(fadeInTimer);
    };
  }, [onComplete, showDocument]);


  console.log('Estado actual:', { isVisible, isFadingOut, progress });

  return (
    <>
      {/* Estilos CSS para animaciones de reserva */}
      <style jsx>{`
        @keyframes fadeToWhite {
          0% { opacity: 1; }
          100% { opacity: 0; }
        }
        
        @keyframes whiteScreenFadeIn {
          0% { opacity: 0; }
          100% { opacity: 1; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
          from { transform: translateX(-100%); }
          to { transform: translateX(0); }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        
        @keyframes documentSlide {
          0% { transform: translateX(-100%) rotate(-5deg); opacity: 0; }
          50% { transform: translateX(0%) rotate(0deg); opacity: 1; }
          100% { transform: translateX(100%) rotate(5deg); opacity: 0; }
        }
        
        @keyframes documentFloat {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-10px) rotate(2deg); }
        }
        
        @keyframes documentProcess {
          0% { transform: scale(1) rotate(0deg); }
          25% { transform: scale(1.05) rotate(1deg); }
          50% { transform: scale(1.1) rotate(0deg); }
          75% { transform: scale(1.05) rotate(-1deg); }
          100% { transform: scale(1) rotate(0deg); }
        }
        
        @keyframes textType {
          0% { width: 0; }
          100% { width: 100%; }
        }
        
        @keyframes stamp {
          0% { transform: scale(0) rotate(-10deg); opacity: 0; }
          50% { transform: scale(1.2) rotate(5deg); opacity: 1; }
          100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }
      `}</style>
      
      <div 
        className="loading-screen-container fixed inset-0 z-50 flex items-center justify-center"
        style={{ 
          background: 'linear-gradient(135deg, #1a365d 0%, #2d3748 100%)',
          opacity: isVisible && !isFadingOut ? 1 : 0,
          transition: isFadingOut ? 'opacity 1.5s ease-out' : 'opacity 2s ease-in'
        }}
      >
      
      {/* Fondo con patrón de papel - con más blur */}
      <div className="absolute inset-0 opacity-5" style={{ filter: 'blur(3px)' }}>
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23d4af37' fill-opacity='0.1'%3E%3Cpath d='M0 0h60v60H0V0zm2 2h56v56H2V2zm2 2h52v52H4V4z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          backgroundSize: '60px 60px'
        }} />
      </div>
      
      {/* Documento de reserva flotante principal - siempre visible con blur */}
      <div className="absolute inset-0 pointer-events-none" style={{ filter: 'blur(1.5px)' }}>
        <div 
          className="absolute w-72 h-40 bg-white rounded-lg shadow-2xl border-2 border-yellow-200 overflow-hidden"
          style={{ 
            top: '8%',
            right: '5%',
            transform: 'rotate(15deg)',
            animation: 'documentFloat 3s ease-in-out infinite'
          }}
        >
          {/* Encabezado del documento */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-3 text-center">
            <h3 className="text-sm font-bold">RESERVA HOTELERA</h3>
            <p className="text-xs opacity-90">AlojaSys</p>
          </div>
          
          {/* Contenido del documento */}
          <div className="p-3 text-gray-700">
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="font-semibold">N°:</span>
                <span className="font-mono">#{Math.floor(Math.random() * 10000)}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-semibold">Estado:</span>
                <span className="text-yellow-600 font-semibold">
                  {progress < 100 ? 'Procesando...' : 'Confirmada'}
                </span>
              </div>
            </div>
            
            {/* Líneas de texto que se escriben */}
            <div className="mt-2 space-y-1">
              <div className="h-1 bg-gray-200 rounded overflow-hidden">
                <div 
                  className="h-full bg-yellow-400 transition-all duration-500"
                  style={{ width: `${Math.min(progress * 1.2, 100)}%` }}
                />
              </div>
            </div>
          </div>
          
          {/* Sello de confirmación */}
          {progress > 80 && (
            <div 
              className="absolute bottom-2 right-2 w-12 h-12 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold"
              style={{ animation: 'stamp 0.8s ease-out' }}
            >
              ✓
            </div>
          )}
        </div>
      </div>

      {/* Ventanas de diferentes módulos del sistema en los costados - con más blur */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ filter: 'blur(2px)' }}>
        {/* Gestión de Habitaciones */}
        <div 
          className="absolute w-28 h-16 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            top: '12%',
            left: '5%',
            transform: 'rotate(-18deg)',
            animation: 'documentFloat 4.2s ease-in-out infinite 0.3s'
          }}
        >
          <div className="p-2 text-xs text-gray-600">
            <div className="font-bold text-purple-600">HABITACIONES</div>
            <div className="text-xs">Ocupadas: 24/30</div>
            <div className="text-xs text-green-600">✓</div>
          </div>
        </div>

        {/* Gráficos y Reportes */}
        <div 
          className="absolute w-28 h-18 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            top: '5%',
            right: '25%',
            transform: 'rotate(22deg)',
            animation: 'documentFloat 3.1s ease-in-out infinite 0.8s'
          }}
        >
          <div className="p-1 text-xs text-gray-600">
            <div className="font-bold text-green-600">ANALYTICS</div>
            <div className="text-xs">Ventas: +15%</div>
            <div className="text-xs text-green-600">📊 📈</div>
          </div>
        </div>

        {/* Check-in/Check-out */}
        <div 
          className="absolute w-32 h-20 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            bottom: '25%',
            left: '3%',
            transform: 'rotate(12deg)',
            animation: 'documentFloat 4.8s ease-in-out infinite 1.2s'
          }}
        >
          <div className="p-2 text-xs text-gray-600">
            <div className="font-bold text-orange-600">CHECK-IN</div>
            <div className="text-xs">Hoy: 12 llegadas</div>
            <div className="text-xs text-blue-600">🏨</div>
          </div>
        </div>

        {/* Facturación */}
        <div 
          className="absolute w-24 h-16 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            bottom: '15%',
            right: '5%',
            transform: 'rotate(-25deg)',
            animation: 'documentFloat 3.6s ease-in-out infinite 1.8s'
          }}
        >
          <div className="p-2 text-xs text-gray-600">
            <div className="font-bold text-red-600">FACTURAS</div>
            <div className="text-xs">Pendientes: 8</div>
            <div className="text-xs text-yellow-600">💰</div>
          </div>
        </div>

        {/* Dashboard */}
        <div 
          className="absolute w-24 h-16 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            top: '18%',
            left: '25%',
            transform: 'rotate(35deg)',
            animation: 'documentFloat 2.8s ease-in-out infinite 2.3s'
          }}
        >
          <div className="p-1 text-xs text-gray-600">
            <div className="font-bold text-indigo-600">DASHBOARD</div>
            <div className="text-xs text-green-600">📊 85%</div>
            <div className="text-xs text-blue-600">📈</div>
          </div>
        </div>

        {/* Clientes */}
        <div 
          className="absolute w-22 h-14 bg-white rounded shadow-lg border border-gray-200"
          style={{ 
            bottom: '35%',
            right: '25%',
            transform: 'rotate(-15deg)',
            animation: 'documentFloat 3.9s ease-in-out infinite 2.7s'
          }}
        >
          <div className="p-1 text-xs text-gray-600">
            <div className="font-bold text-teal-600">CLIENTES</div>
            <div className="text-xs">Activos: 156</div>
            <div className="text-xs text-blue-600">👥</div>
          </div>
        </div>
      </div>
      
      {/* Pantalla blanca de transición */}
      {showWhiteScreen && (
        <div 
          className="fixed inset-0 z-50 bg-white flex items-center justify-center"
          style={{ 
            animation: 'whiteScreenFadeIn 0.8s ease-in-out'
          }}
        >
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4">
              <div className="w-full h-full border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
            <p className="text-gray-600 text-lg font-light">Cargando sistema...</p>
          </div>
        </div>
      )}
      
      {/* Contenido principal */}
      <div className="text-center relative z-10">
        {/* Logo y título */}
        <div className="mb-16" style={{ animation: 'fadeInUp 1s ease-out' }}>
          <h1 
            className="text-7xl font-light mb-6 tracking-wide" 
            style={{ 
              background: 'linear-gradient(135deg, #1a365d 0%, #d4af37 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              animation: 'pulse 4s ease-in-out infinite'
            }}
          >
            AlojaSys
          </h1>
          <p className="text-xl text-gray-300 font-light tracking-wider">
            Sistema de Gestión Hotelera
          </p>
        </div>
        
        {/* Spinner temático de procesamiento */}
        <div className="mb-12" style={{ animation: 'fadeInUp 1s ease-out 0.3s both' }}>
          <div className="relative w-20 h-20 mx-auto">
            {/* Círculo exterior */}
            <div className="absolute inset-0 border-2 border-gray-600 rounded-full"></div>
            
            {/* Círculo de carga principal */}
            <div 
              className="absolute inset-0 border-2 border-transparent border-t-yellow-400 rounded-full animate-spin"
              style={{ animationDuration: '2s' }}
            ></div>
            
            {/* Círculo interior */}
            <div 
              className="absolute inset-2 border border-transparent border-r-yellow-300 rounded-full animate-spin"
              style={{ animationDuration: '3s', animationDirection: 'reverse' }}
            ></div>
            
            {/* Icono de documento */}
            <div 
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-yellow-400 text-2xl"
              style={{ animation: 'documentProcess 2s ease-in-out infinite' }}
            >
              📄
            </div>
          </div>
        </div>
        
        {/* Barra de progreso */}
        <div className="w-96 h-2 bg-gray-700 rounded-full overflow-hidden mb-8 relative mx-auto" style={{ animation: 'fadeInUp 1s ease-out 0.6s both' }}>
          <div 
            className="h-full transition-all duration-700 ease-out rounded-full relative"
            style={{ 
              width: `${progress}%`,
              background: 'linear-gradient(90deg, #1a365d 0%, #d4af37 100%)'
            }}
          >
            <div 
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30"
              style={{ 
                animation: 'shimmer 2s infinite',
                transform: 'translateX(-100%)'
              }}
            />
          </div>
        </div>
        
        {/* Texto de procesamiento dinámico */}
        <div className="mb-4" style={{ animation: 'fadeInUp 1s ease-out 0.9s both' }}>
          <p className="text-gray-400 text-lg font-light tracking-wide mb-2">
            {reservationSteps[currentStep]}
          </p>
        </div>
        
        {/* Porcentaje */}
        <p className="text-gray-500 text-sm font-mono tracking-wider" style={{ animation: 'fadeInUp 1s ease-out 1.2s both' }}>
          {Math.round(progress)}%
        </p>
      </div>
      
      {/* Elementos decorativos */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Líneas decorativas */}
        <div className="absolute top-1/4 left-0 w-32 h-px bg-gradient-to-r from-transparent via-yellow-400 to-transparent opacity-30" 
             style={{ animation: 'slideIn 2s ease-out 1.5s both' }} />
        <div className="absolute top-1/4 right-0 w-32 h-px bg-gradient-to-l from-transparent via-yellow-400 to-transparent opacity-30" 
             style={{ animation: 'slideIn 2s ease-out 1.7s both' }} />
        <div className="absolute bottom-1/4 left-0 w-32 h-px bg-gradient-to-r from-transparent via-yellow-400 to-transparent opacity-30" 
             style={{ animation: 'slideIn 2s ease-out 1.9s both' }} />
        <div className="absolute bottom-1/4 right-0 w-32 h-px bg-gradient-to-l from-transparent via-yellow-400 to-transparent opacity-30" 
             style={{ animation: 'slideIn 2s ease-out 2.1s both' }} />
      </div>
      </div>
    </>
  );
};

export default LoadingScreen;
