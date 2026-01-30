// Helpers para ordenar habitaciones por número de forma “humana”
// (evita el orden lexicográfico: 1, 10, 11, 2…)

const toFiniteInt = (value) => {
  if (value == null) return null;
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  // Truncamos para evitar floats raros (p.ej. "1.0")
  return Math.trunc(n);
};

const extractFirstIntFromString = (value) => {
  const s = String(value ?? "");
  const m = s.match(/(\d+)/);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) ? Math.trunc(n) : null;
};

export const getRoomNumberLike = (room) => {
  // Prioridad: campo number (si existe) → número embebido en name
  const direct = toFiniteInt(room?.number);
  if (direct != null) return direct;
  return extractFirstIntFromString(room?.name);
};

export const getRoomSortKey = (room) => {
  // Orden por: piso → número → nombre → id
  const floor = toFiniteInt(room?.floor) ?? 0;
  const num = getRoomNumberLike(room);
  const numKey = (num == null ? Number.MAX_SAFE_INTEGER : num);
  const nameKey = String(room?.name ?? "").toLowerCase();
  const idKey = String(room?.id ?? "");

  // Padding para que "2" < "10" en comparación lexicográfica
  const floorPart = String(floor).padStart(4, "0");
  const numPart = String(numKey).padStart(8, "0");
  return `${floorPart}|${numPart}|${nameKey}|${idKey}`;
};

export const sortRooms = (rooms = []) => {
  const list = Array.isArray(rooms) ? rooms.slice() : [];
  list.sort((a, b) =>
    getRoomSortKey(a).localeCompare(getRoomSortKey(b), undefined, {
      numeric: true,
      sensitivity: "base",
    })
  );
  return list;
};

