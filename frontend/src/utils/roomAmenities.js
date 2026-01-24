// Lista “máxima útil” de amenities por habitación.
// Guardamos en backend un array de strings (códigos). Los custom se guardan como "custom:<texto>".

export const ROOM_AMENITIES = [
  // Conectividad / tecnología
  { code: 'wifi', i18nKey: 'rooms_modal.amenities.items.wifi', categoryKey: 'connectivity' },
  { code: 'wired_internet', i18nKey: 'rooms_modal.amenities.items.wired_internet', categoryKey: 'connectivity' },
  { code: 'smart_tv', i18nKey: 'rooms_modal.amenities.items.smart_tv', categoryKey: 'connectivity' },
  { code: 'tv', i18nKey: 'rooms_modal.amenities.items.tv', categoryKey: 'connectivity' },
  { code: 'streaming_services', i18nKey: 'rooms_modal.amenities.items.streaming_services', categoryKey: 'connectivity' },
  { code: 'cable_tv', i18nKey: 'rooms_modal.amenities.items.cable_tv', categoryKey: 'connectivity' },
  { code: 'workspace', i18nKey: 'rooms_modal.amenities.items.workspace', categoryKey: 'connectivity' },
  { code: 'socket_near_bed', i18nKey: 'rooms_modal.amenities.items.socket_near_bed', categoryKey: 'connectivity' },
  { code: 'usb_chargers', i18nKey: 'rooms_modal.amenities.items.usb_chargers', categoryKey: 'connectivity' },
  { code: 'bluetooth_speaker', i18nKey: 'rooms_modal.amenities.items.bluetooth_speaker', categoryKey: 'connectivity' },

  // Climatización / confort
  { code: 'air_conditioning', i18nKey: 'rooms_modal.amenities.items.air_conditioning', categoryKey: 'comfort' },
  { code: 'heating', i18nKey: 'rooms_modal.amenities.items.heating', categoryKey: 'comfort' },
  { code: 'ceiling_fan', i18nKey: 'rooms_modal.amenities.items.ceiling_fan', categoryKey: 'comfort' },
  { code: 'blackout_curtains', i18nKey: 'rooms_modal.amenities.items.blackout_curtains', categoryKey: 'comfort' },
  { code: 'soundproofing', i18nKey: 'rooms_modal.amenities.items.soundproofing', categoryKey: 'comfort' },
  { code: 'safe', i18nKey: 'rooms_modal.amenities.items.safe', categoryKey: 'comfort' },
  { code: 'iron', i18nKey: 'rooms_modal.amenities.items.iron', categoryKey: 'comfort' },
  { code: 'iron_board', i18nKey: 'rooms_modal.amenities.items.iron_board', categoryKey: 'comfort' },
  { code: 'wardrobe', i18nKey: 'rooms_modal.amenities.items.wardrobe', categoryKey: 'comfort' },
  { code: 'clothes_rack', i18nKey: 'rooms_modal.amenities.items.clothes_rack', categoryKey: 'comfort' },
  { code: 'mosquito_net', i18nKey: 'rooms_modal.amenities.items.mosquito_net', categoryKey: 'comfort' },
  { code: 'fireplace', i18nKey: 'rooms_modal.amenities.items.fireplace', categoryKey: 'comfort' },
  { code: 'private_entrance', i18nKey: 'rooms_modal.amenities.items.private_entrance', categoryKey: 'comfort' },

  // Baño
  { code: 'private_bathroom', i18nKey: 'rooms_modal.amenities.items.private_bathroom', categoryKey: 'bathroom' },
  { code: 'shower', i18nKey: 'rooms_modal.amenities.items.shower', categoryKey: 'bathroom' },
  { code: 'bathtub', i18nKey: 'rooms_modal.amenities.items.bathtub', categoryKey: 'bathroom' },
  { code: 'jacuzzi', i18nKey: 'rooms_modal.amenities.items.jacuzzi', categoryKey: 'bathroom' },
  { code: 'bidet', i18nKey: 'rooms_modal.amenities.items.bidet', categoryKey: 'bathroom' },
  { code: 'hairdryer', i18nKey: 'rooms_modal.amenities.items.hairdryer', categoryKey: 'bathroom' },
  { code: 'towels', i18nKey: 'rooms_modal.amenities.items.towels', categoryKey: 'bathroom' },
  { code: 'toiletries', i18nKey: 'rooms_modal.amenities.items.toiletries', categoryKey: 'bathroom' },
  { code: 'bathrobe', i18nKey: 'rooms_modal.amenities.items.bathrobe', categoryKey: 'bathroom' },
  { code: 'slippers', i18nKey: 'rooms_modal.amenities.items.slippers', categoryKey: 'bathroom' },
  { code: 'bed_linen', i18nKey: 'rooms_modal.amenities.items.bed_linen', categoryKey: 'bathroom' },

  // Cocina / minibar
  { code: 'kitchenette', i18nKey: 'rooms_modal.amenities.items.kitchenette', categoryKey: 'kitchen' },
  { code: 'kitchen', i18nKey: 'rooms_modal.amenities.items.kitchen', categoryKey: 'kitchen' },
  { code: 'refrigerator', i18nKey: 'rooms_modal.amenities.items.refrigerator', categoryKey: 'kitchen' },
  { code: 'minibar', i18nKey: 'rooms_modal.amenities.items.minibar', categoryKey: 'kitchen' },
  { code: 'microwave', i18nKey: 'rooms_modal.amenities.items.microwave', categoryKey: 'kitchen' },
  { code: 'coffee_maker', i18nKey: 'rooms_modal.amenities.items.coffee_maker', categoryKey: 'kitchen' },
  { code: 'kettle', i18nKey: 'rooms_modal.amenities.items.kettle', categoryKey: 'kitchen' },
  { code: 'dishes', i18nKey: 'rooms_modal.amenities.items.dishes', categoryKey: 'kitchen' },
  { code: 'stovetop', i18nKey: 'rooms_modal.amenities.items.stovetop', categoryKey: 'kitchen' },
  { code: 'oven', i18nKey: 'rooms_modal.amenities.items.oven', categoryKey: 'kitchen' },
  { code: 'toaster', i18nKey: 'rooms_modal.amenities.items.toaster', categoryKey: 'kitchen' },
  { code: 'dining_area', i18nKey: 'rooms_modal.amenities.items.dining_area', categoryKey: 'kitchen' },

  // Exterior / vistas
  { code: 'balcony', i18nKey: 'rooms_modal.amenities.items.balcony', categoryKey: 'outdoor' },
  { code: 'terrace', i18nKey: 'rooms_modal.amenities.items.terrace', categoryKey: 'outdoor' },
  { code: 'patio', i18nKey: 'rooms_modal.amenities.items.patio', categoryKey: 'outdoor' },
  { code: 'garden_view', i18nKey: 'rooms_modal.amenities.items.garden_view', categoryKey: 'outdoor' },
  { code: 'sea_view', i18nKey: 'rooms_modal.amenities.items.sea_view', categoryKey: 'outdoor' },
  { code: 'mountain_view', i18nKey: 'rooms_modal.amenities.items.mountain_view', categoryKey: 'outdoor' },
  { code: 'city_view', i18nKey: 'rooms_modal.amenities.items.city_view', categoryKey: 'outdoor' },

  // Accesibilidad / seguridad
  { code: 'wheelchair_accessible', i18nKey: 'rooms_modal.amenities.items.wheelchair_accessible', categoryKey: 'accessibility' },
  { code: 'ground_floor', i18nKey: 'rooms_modal.amenities.items.ground_floor', categoryKey: 'accessibility' },
  { code: 'elevator_access', i18nKey: 'rooms_modal.amenities.items.elevator_access', categoryKey: 'accessibility' },
  { code: 'smoke_detector', i18nKey: 'rooms_modal.amenities.items.smoke_detector', categoryKey: 'safety' },
  { code: 'fire_extinguisher', i18nKey: 'rooms_modal.amenities.items.fire_extinguisher', categoryKey: 'safety' },
  { code: 'first_aid_kit', i18nKey: 'rooms_modal.amenities.items.first_aid_kit', categoryKey: 'safety' },
  { code: 'carbon_monoxide_detector', i18nKey: 'rooms_modal.amenities.items.carbon_monoxide_detector', categoryKey: 'safety' },

  // Camas
  { code: 'single_bed', i18nKey: 'rooms_modal.amenities.items.single_bed', categoryKey: 'beds' },
  { code: 'double_bed', i18nKey: 'rooms_modal.amenities.items.double_bed', categoryKey: 'beds' },
  { code: 'queen_bed', i18nKey: 'rooms_modal.amenities.items.queen_bed', categoryKey: 'beds' },
  { code: 'king_bed', i18nKey: 'rooms_modal.amenities.items.king_bed', categoryKey: 'beds' },
  { code: 'sofa_bed', i18nKey: 'rooms_modal.amenities.items.sofa_bed', categoryKey: 'beds' },
  { code: 'bunk_bed', i18nKey: 'rooms_modal.amenities.items.bunk_bed', categoryKey: 'beds' },
  { code: 'crib', i18nKey: 'rooms_modal.amenities.items.crib', categoryKey: 'beds' },
]

export const ROOM_AMENITY_CATEGORIES = [
  { key: 'connectivity', i18nKey: 'rooms_modal.amenities.categories.connectivity' },
  { key: 'comfort', i18nKey: 'rooms_modal.amenities.categories.comfort' },
  { key: 'bathroom', i18nKey: 'rooms_modal.amenities.categories.bathroom' },
  { key: 'kitchen', i18nKey: 'rooms_modal.amenities.categories.kitchen' },
  { key: 'outdoor', i18nKey: 'rooms_modal.amenities.categories.outdoor' },
  { key: 'accessibility', i18nKey: 'rooms_modal.amenities.categories.accessibility' },
  { key: 'safety', i18nKey: 'rooms_modal.amenities.categories.safety' },
  { key: 'beds', i18nKey: 'rooms_modal.amenities.categories.beds' },
]

export function normalizeAmenityCode(code) {
  return String(code || '').trim()
}

export function isCustomAmenity(code) {
  return normalizeAmenityCode(code).toLowerCase().startsWith('custom:')
}

export function getCustomAmenityLabel(code) {
  const raw = normalizeAmenityCode(code)
  if (!isCustomAmenity(raw)) return raw
  return raw.slice('custom:'.length).trim() || raw
}

export function getAmenityLabel(t, code) {
  const normalized = normalizeAmenityCode(code)
  if (!normalized) return ''
  if (isCustomAmenity(normalized)) return getCustomAmenityLabel(normalized)
  const found = ROOM_AMENITIES.find((a) => a.code === normalized)
  return found ? t(found.i18nKey) : normalized
}

