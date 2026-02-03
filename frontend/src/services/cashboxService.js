import fetchWithAuth from "./fetchWithAuth";
import { getApiURL, getApiParams } from "./utils";

const base = () => `${getApiURL()}/api/cashbox`;

export const cashboxService = {
  getCurrentSession: ({ hotelId, currency = "ARS" }) => {
    return fetchWithAuth(`${base()}/sessions/current/${getApiParams({ hotel_id: hotelId, currency })}`);
  },

  getSession: ({ sessionId }) => {
    return fetchWithAuth(`${base()}/sessions/${sessionId}/`);
  },

  openSession: ({ hotelId, openingAmount = 0, currency = "ARS", notes = "" }) => {
    return fetchWithAuth(`${base()}/sessions/`, {
      method: "POST",
      body: JSON.stringify({
        hotel_id: Number(hotelId),
        opening_amount: openingAmount,
        currency,
        notes,
      }),
    });
  },

  closeSession: ({ sessionId, closingAmount, notes = "" }) => {
    return fetchWithAuth(`${base()}/sessions/${sessionId}/close/`, {
      method: "POST",
      body: JSON.stringify({ closing_amount: closingAmount, notes }),
    });
  },

  listSessions: ({ hotelId, status, currency = "ARS" } = {}) => {
    return fetchWithAuth(`${base()}/sessions/${getApiParams({ hotel_id: hotelId, status, currency })}`);
  },

  listMovements: ({ hotelId, sessionId } = {}) => {
    return fetchWithAuth(`${base()}/movements/${getApiParams({ hotel_id: hotelId, session_id: sessionId })}`);
  },

  createMovement: ({ sessionId, hotelId, movementType, amount, currency = "ARS", description = "" }) => {
    return fetchWithAuth(`${base()}/movements/`, {
      method: "POST",
      body: JSON.stringify({
        session: Number(sessionId),
        hotel: Number(hotelId),
        movement_type: movementType,
        amount,
        currency,
        description,
      }),
    });
  },
};

