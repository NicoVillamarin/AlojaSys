import { Outlet } from "react-router-dom";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import Sidebar from "src/components/Sidebar";
import Navbar from "src/components/Navbar";
import { useSidebar } from "src/hooks/useSidebar";

export default function MainLayout() {
  const { 
    isCollapsed, 
    isMini, 
    sidebarWidth, 
    isResizing, 
    isMobileOpen, 
    isMobile, 
    toggleCollapse, 
    toggleMini, 
    resetWidth, 
    forceOpen, 
    toggleMobile, 
    closeMobile, 
    startResizing 
  } = useSidebar();

  return (
    <div className="h-screen w-full bg-aloja-gray-50 relative overflow-hidden">
      {/* Overlay invisible para cerrar tocando fuera del sidebar en móvil */}
      {isMobile && isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 md:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar - Desktop */}
      <div 
        className={`hidden md:block fixed left-0 top-0 h-screen z-20 transition-all duration-300 ${
          isCollapsed ? 'w-0' : ''
        }`}
        style={{ 
          width: isCollapsed ? '0px' : isMini ? '75px' : `${sidebarWidth}px`,
          transition: isResizing ? 'none' : 'all 0.3s ease'
        }}
      >
        <Sidebar 
          isCollapsed={isCollapsed}
          isMini={isMini}
          onToggleCollapse={toggleCollapse}
          onToggleMini={toggleMini}
          onResetWidth={resetWidth}
          onForceOpen={forceOpen}
        />
      </div>

      {/* Sidebar - Móvil */}
      <div 
        className={`md:hidden fixed left-0 top-0 h-screen z-50 w-64 transform transition-transform duration-300 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar 
          isCollapsed={false}
          isMini={false}
          onToggleCollapse={closeMobile}
          onToggleMini={closeMobile}
          onResetWidth={resetWidth}
          onForceOpen={forceOpen}
          isMobile={true}
          onMobileClose={closeMobile}
        />
      </div>

      {/* Handle de redimensionamiento */}
      {!isCollapsed && !isMini && (
        <div 
          className="hidden md:block fixed top-0 w-1 h-screen bg-gray-300 hover:bg-aloja-gold transition-colors cursor-col-resize z-30"
          style={{ left: `${sidebarWidth}px` }}
          onMouseDown={startResizing}
        />
      )}

      {/* Botón para cerrar cuando está en modo normal */}
      {!isCollapsed && !isMini && (
        <button
          onClick={toggleCollapse}
          className="hidden md:block fixed top-1/2 transform -translate-y-1/2 z-40 bg-aloja-navy text-white p-1.5 rounded-e-full shadow-lg hover:bg-aloja-navy/90 transition-colors"
          style={{ left: `${sidebarWidth - 5}px` }}
          title="Minimizar sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}

      {/* Botón para expandir cuando está en modo mini */}
      {isMini && (
        <button
          onClick={toggleCollapse}
          className="hidden md:block fixed top-1/2 transform -translate-y-1/2 z-40 bg-aloja-navy text-white p-1.5 rounded-e-full shadow-lg hover:bg-aloja-navy/90 transition-colors"
          style={{ left: '65px' }}
          title="Expandir sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Botón de emergencia para abrir sidebar cuando está colapsado */}
      {isCollapsed && (
        <button
          onClick={forceOpen}
          className="hidden md:block fixed left-2 top-1/2 transform -translate-y-1/2 z-40 bg-aloja-navy text-white p-1.5 rounded-full shadow-lg hover:bg-aloja-navy/90 transition-colors border-2 border-white"
          title="Abrir sidebar"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Contenido principal */}
      <div 
        className={`flex flex-col h-screen transition-all duration-300 ${
          isMobile && isMobileOpen ? 'blur-[2px]' : ''
        }`}
        style={{ 
          marginLeft: isMobile ? '0px' : (isCollapsed ? '0px' : isMini ? '75px' : `${sidebarWidth}px`),
          transition: isResizing ? 'none' : 'all 0.3s ease'
        }}
      >
        <Navbar 
          onToggleMobile={toggleMobile}
          isMobile={isMobile}
        />
        <main className="flex-1 overflow-y-auto py-6 px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}


