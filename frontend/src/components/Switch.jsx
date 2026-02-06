import React from "react";

/**
 * Switch (toggle) reutilizable y accesible.
 *
 * Props:
 * - checked: boolean
 * - onChange: (nextChecked: boolean) => void
 * - label?: string
 * - description?: string
 * - disabled?: boolean
 * - size?: "sm" | "md"
 * - className?: string
 */
export default function Switch({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  size = "md",
  className = "",
}) {
  const track =
    size === "sm" ? "w-9 h-5 p-[2px]" : "w-11 h-6 p-[2px]";
  const thumb = size === "sm" ? "w-4 h-4" : "w-5 h-5";
  const translate = size === "sm" ? "translate-x-4" : "translate-x-5";

  const handleToggle = () => {
    if (disabled) return;
    if (typeof onChange === "function") onChange(!checked);
  };

  return (
    <div className={["inline-flex items-center gap-3", className].join(" ")}>
      {(label || description) && (
        <div className="min-w-0">
          {label && (
            <div className="text-sm font-medium text-slate-800 leading-5">
              {label}
            </div>
          )}
          {description && (
            <div className="text-xs text-slate-500 leading-4">
              {description}
            </div>
          )}
        </div>
      )}

      <button
        type="button"
        role="switch"
        aria-checked={!!checked}
        disabled={disabled}
        onClick={handleToggle}
        className={[
          "relative inline-flex shrink-0 items-center rounded-full transition-colors",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-aloja-navy/30",
          track,
          disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer",
          checked ? "bg-aloja-navy" : "bg-slate-300",
        ].join(" ")}
      >
        <span
          aria-hidden="true"
          className={[
            "block rounded-full bg-white shadow-sm transition-transform",
            thumb,
            checked ? translate : "translate-x-0",
          ].join(" ")}
        />
      </button>
    </div>
  );
}

