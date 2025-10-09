import fetchWithAuth from "./fetchWithAuth";
import { getApiURL } from "./utils";

const base = () => `${getApiURL()}/api/payments`;

export async function createPreference({ reservationId, amount }) {
  if (!reservationId) throw new Error("reservationId es requerido");
  const url = `${base()}/checkout-preference/`;
  const body = amount ? { reservation_id: reservationId, amount } : { reservation_id: reservationId };
  return await fetchWithAuth(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// Placeholder para Payment Brick (cuando implementemos intent específico)
export async function createBrickIntent({ reservationId, amount }) {
  if (!reservationId) throw new Error("reservationId es requerido");
  const url = `${base()}/brick-intent/`;
  const body = amount ? { reservation_id: reservationId, amount } : { reservation_id: reservationId };
  return await fetchWithAuth(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// Utilidad opcional: obtener init_point y abrirlo en nueva pestaña (Checkout Pro)
export async function openCheckoutPro({ reservationId, amount }) {
  const pref = await createPreference({ reservationId, amount });
  const url = pref?.sandbox_init_point || pref?.init_point;
  if (!url) throw new Error("No se obtuvo init_point");
  window.open(url, "_blank");
  return pref;
}


