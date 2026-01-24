import React, { useEffect, useRef, useState } from "react";
import Button from "src/components/Button";
import { Chevron } from "src/assets/icons/Chevron";

/**
 * ActionMenuButton
 * Botón reutilizable con menú desplegable de acciones.
 *
 * items: [{ key, label, onClick, disabled?, leftIcon?, className? }]
 */
export default function ActionMenuButton({
  label,
  items = [],
  variant = "success",
  size = "md",
  disabled = false,
  isPending = false,
  loadingText,
  leftIcon,
  className = "",
  menuClassName = "",
  align = "right", // right | left
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, []);

  const hasEnabledItem = (items || []).some((it) => !it?.disabled);
  const isDisabled = disabled || isPending || !hasEnabledItem;

  return (
    <div className={`relative ${className}`} ref={ref}>
      <Button
        variant={variant}
        size={size}
        disabled={isDisabled}
        isPending={isPending}
        loadingText={loadingText}
        onClick={() => setOpen((v) => !v)}
        leftIcon={leftIcon}
      >
        <div className="flex items-center gap-2">
          <span>{label}</span>
          <span className={variant === "primary" ? "text-white" : ""}>
            <Chevron open={open} />
          </span>
        </div>
      </Button>

      {open && (
        <div
          className={`absolute ${
            align === "left" ? "left-0" : "right-0"
          } mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-30 overflow-hidden ${menuClassName}`}
          role="menu"
        >
          {(items || []).map((it, idx) => {
            const itemDisabled = Boolean(it?.disabled);
            return (
              <button
                key={it?.key ?? idx}
                type="button"
                role="menuitem"
                disabled={itemDisabled}
                onClick={() => {
                  if (itemDisabled) return;
                  setOpen(false);
                  it?.onClick?.();
                }}
                className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
                  itemDisabled
                    ? "opacity-50 cursor-not-allowed"
                    : "hover:bg-gray-50 cursor-pointer"
                } ${idx > 0 ? "border-t border-gray-100" : ""} ${
                  it?.className || ""
                }`}
              >
                {it?.leftIcon ? <span className="shrink-0">{it.leftIcon}</span> : null}
                <span className="flex-1">{it?.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

