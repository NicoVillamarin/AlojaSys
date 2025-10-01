import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import Button from "src/components/Button";

const modalRootId = "__aloja_modal_root";

function ensureModalRoot() {
  let root = document.getElementById(modalRootId);
  if (!root) {
    root = document.createElement("div");
    root.id = modalRootId;
    document.body.appendChild(root);
  }
  return root;
}

function useLockBodyScroll(locked) {
  useEffect(() => {
    if (!locked) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = original;
    };
  }, [locked]);
}

export default function ModalLayout({
  isOpen,
  onClose,
  size = "md", // sm | md | lg | xl | full
  children,
  backdrop = true,
  closeOnBackdrop = true,
  labelledBy,
  describedBy,
  title,
  header,
  onSubmit,
  submitText = "Guardar",
  cancelText = "Cancelar",
  submitDisabled = false,
  customFooter,
  submitLoading = false,
  isDetail = false,
}) {
  const root = ensureModalRoot();
  const dialogRef = useRef(null);
  const [render, setRender] = useState(isOpen);
  const [show, setShow] = useState(isOpen);

  useLockBodyScroll(isOpen);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || !dialogRef.current) return;
    const previouslyFocused = document.activeElement;
    dialogRef.current.focus();
    return () => previouslyFocused?.focus?.();
  }, [isOpen]);

  // Animación de salida: mantener montado y desmontar al finalizar la animación
  useEffect(() => {
    if (isOpen) {
      setRender(true);
      const id = requestAnimationFrame(() => setShow(true));
      return () => cancelAnimationFrame(id);
    } else {
      setShow(false);
    }
  }, [isOpen]);

  const onBackdropClick = (e) => {
    if (!closeOnBackdrop) return;
    if (e.target === e.currentTarget) onClose?.();
  };

  const sizes = {
    sm: "max-w-sm w-full",
    md: "max-w-md w-full", 
    wmedium: "w-1/2",
    lg: "max-w-2xl w-full",
    lg2: "w-3/4",
    xl: "max-w-4xl w-full",
    full: "max-w-[95vw] w-full",
  };

  if (!render) return null;

  const backdropAnim = show
    ? "opacity-0 animate-[fadeIn_200ms_ease_forwards]"
    : "opacity-100 animate-[fadeOut_180ms_ease_forwards]";
  const panelAnim = show
    ? "opacity-0 translate-y-4 sm:translate-y-0 scale-[0.98] animate-[popIn_240ms_cubic-bezier(0.2,0.8,0.2,1)_forwards]"
    : "opacity-100 translate-y-0 scale-100 animate-[popOut_180ms_cubic-bezier(0.4,0.0,0.2,1)_forwards]";

  return createPortal(
    (
      <div
        className="fixed inset-0 z-[1000] flex items-start justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        onMouseDown={onBackdropClick}
      >
        {backdrop && (
          <div className={`absolute inset-0 bg-black/45 backdrop-blur-sm ${backdropAnim}`} />
        )}

        {/* Contenedor de scroll sobre el backdrop (el backdrop no scrollea) */}
        <div className="relative z-10 w-full h-full flex justify-center items-start overflow-y-auto py-10 px-4">
          <div
            ref={dialogRef}
            tabIndex={-1}
            className={`relative ${sizes[size]} bg-white rounded-2xl shadow-2xl ring-1 ring-black/5 outline-none flex flex-col ${panelAnim}`}
            style={{
              marginTop: 'auto',
              marginBottom: 'auto',
              minHeight: 'fit-content'
            }}
            onAnimationEnd={(e) => {
              if (!show && e.animationName === 'popOut') {
                setRender(false);
              }
            }}
          >
          {(header || title) && (
            <div className="flex items-center justify-between gap-4 px-5 pt-4 pb-3 border-b border-gray-100">
              <div className="text-base font-semibold text-aloja-navy" id={labelledBy}>
                {header || title}
              </div>
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className="inline-flex items-center justify-center w-8 h-8 rounded-full text-aloja-gray-800/70 hover:bg-gray-100"
                  aria-label="Cerrar"
                >
                  <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </button>
              )}
            </div>
          )}

          <div className="flex-1 px-5 py-4 text-sm text-aloja-gray-800" id={describedBy}>
            {children}
          </div>

          {(customFooter || onSubmit || onClose) && (
            <div className="px-5 pt-2 pb-4 border-t border-gray-100 flex items-center justify-end gap-2">
              {customFooter ? (
                customFooter
              ) : (
                <>
                  {onClose && (
                    <Button variant="danger" size="md" onClick={onClose}>
                      {cancelText}
                    </Button>
                  )}
                  {onSubmit && !isDetail && (
                    <Button
                      variant="success"
                      size="md"
                      disabled={submitDisabled}
                      onClick={onSubmit}
                      loadingText={submitLoading}
                    >
                      {submitText}
                    </Button>
                  )}
                </>
              )}
            </div>
          )}
          </div>
        </div>

        <style>{`
@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
@keyframes fadeOut { from { opacity: 1 } to { opacity: 0 } }
@keyframes popIn { from { opacity: 0; transform: translateY(16px) scale(0.98) } to { opacity: 1; transform: translateY(0) scale(1) } }
@keyframes popOut { from { opacity: 1; transform: translateY(0) scale(1) } to { opacity: 0; transform: translateY(16px) scale(0.98) } }
        `}</style>
      </div>
    ),
    root
  );
}

ModalLayout.Header = function Header({ children, onClose }) {
  return (
    <div className="flex items-center justify-between gap-4 px-5 pt-4 pb-3 border-b border-gray-100">
      <div className="text-base font-semibold text-aloja-navy">{children}</div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="inline-flex items-center justify-center w-8 h-8 rounded-full text-aloja-gray-800/70 hover:bg-gray-100"
          aria-label="Cerrar"
        >
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  );
};

ModalLayout.Body = function Body({ children }) {
  return <div className="px-5 py-4 text-sm text-aloja-gray-800">{children}</div>;
};

ModalLayout.Footer = function Footer({ children }) {
  return <div className="px-5 pt-2 pb-4 border-t border-gray-100 flex items-center justify-end gap-2">{children}</div>;
};

ModalLayout.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func,
  size: PropTypes.oneOf(["sm", "md", "lg", "xl", "full"]),
  children: PropTypes.node,
  backdrop: PropTypes.bool,
  closeOnBackdrop: PropTypes.bool,
  labelledBy: PropTypes.string,
  describedBy: PropTypes.string,
  title: PropTypes.node,
  header: PropTypes.node,
  onSubmit: PropTypes.func,
  submitText: PropTypes.node,
  cancelText: PropTypes.node,
  submitDisabled: PropTypes.bool,
  customFooter: PropTypes.node,
};


