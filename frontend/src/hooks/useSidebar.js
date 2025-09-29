import { useState, useEffect, useCallback } from 'react';

export const useSidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    // Recuperar el estado de colapso del localStorage
    const saved = localStorage.getItem('sidebar-collapsed');
    return saved ? JSON.parse(saved) : false;
  });

  const [sidebarWidth, setSidebarWidth] = useState(() => {
    // Recuperar el ancho guardado del localStorage o usar el valor por defecto
    const saved = localStorage.getItem('sidebar-width');
    return saved ? parseInt(saved) : 256; // 256px = w-64 por defecto
  });

  const [isMini, setIsMini] = useState(() => {
    // Recuperar el estado mini del localStorage
    const saved = localStorage.getItem('sidebar-mini');
    return saved ? JSON.parse(saved) : false;
  });

  const [isResizing, setIsResizing] = useState(false);

  // Guardar cambios en localStorage
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  useEffect(() => {
    localStorage.setItem('sidebar-width', sidebarWidth.toString());
  }, [sidebarWidth]);

  useEffect(() => {
    localStorage.setItem('sidebar-mini', JSON.stringify(isMini));
  }, [isMini]);

  const toggleCollapse = () => {
    if (isMini) {
      // Si está en modo mini, cambiar a normal
      setIsMini(false);
      setIsCollapsed(false);
    } else if (isCollapsed) {
      // Si está colapsado, cambiar a normal
      setIsCollapsed(false);
    } else {
      // Si está normal, cambiar a mini
      setIsMini(true);
    }
  };

  const toggleMini = () => {
    setIsMini(!isMini);
    if (isCollapsed) {
      setIsCollapsed(false);
    }
  };

  const resetWidth = () => {
    setSidebarWidth(256);
    setIsCollapsed(false);
    setIsMini(false);
  };

  const forceOpen = () => {
    setIsCollapsed(false);
    setIsMini(false);
  };

  const startResizing = useCallback((e) => {
    setIsResizing(true);
    e.preventDefault();
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e) => {
    if (!isResizing) return;
    
    const newWidth = e.clientX;
    const minWidth = 200;
    const maxWidth = 400;
    
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
    }
  }, [isResizing]);

  // Event listeners para el redimensionamiento
  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', resize);
      document.addEventListener('mouseup', stopResizing);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResizing);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.removeEventListener('mousemove', resize);
      document.removeEventListener('mouseup', stopResizing);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, resize, stopResizing]);

  return {
    isCollapsed,
    isMini,
    sidebarWidth,
    isResizing,
    toggleCollapse,
    toggleMini,
    resetWidth,
    forceOpen,
    startResizing
  };
};
