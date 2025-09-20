import { toast } from "react-toastify";
import React from "react";

export const showSuccess = (message, options = {}) =>
  toast.success(message, { position: "top-right", autoClose: 2500, ...options });

// Error que requiere aceptación explícita (sin autocierre)
export const showErrorConfirm = (message, options = {}) =>
  toast.error(({ closeToast }) => (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div>{message}</div>
      <button
        onClick={closeToast}
        style={{
          alignSelf: "flex-end",
          background: "#ef4444",
          color: "#fff",
          borderRadius: 6,
          padding: "6px 12px",
          border: 0,
          cursor: "pointer",
        }}
      >
        Aceptar
      </button>
    </div>
  ), {
    position: "top-right",
    autoClose: false,
    closeOnClick: false,
    draggable: false,
    closeButton: false,
    ...options,
  });


