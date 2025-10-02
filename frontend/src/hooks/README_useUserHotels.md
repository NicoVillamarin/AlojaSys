# useUserHotels Hook

Hook para acceder a los hoteles asignados al usuario logueado y filtrar componentes según sus permisos.

## 📖 Uso básico

```jsx
import { useUserHotels } from 'src/hooks/useUserHotels'

function MyComponent() {
  const { hotelIds, hotelIdsString, isSuperuser } = useUserHotels()
  
  // hotelIds: [1, 2, 3]
  // hotelIdsString: "1,2,3"
  // isSuperuser: false
}
```

## ✅ Filtrar SelectAsync por hoteles del usuario

### Ejemplo 1: Filtrar hoteles en un selector

```jsx
import { useUserHotels } from 'src/hooks/useUserHotels'
import SelectAsync from 'src/components/selects/SelectAsync'

function CreateReservationModal() {
  const { hotelIdsString, isSuperuser } = useUserHotels()
  
  return (
    <SelectAsync
      title="Hotel *"
      name="hotel"
      resource="hotels"
      placeholder="Seleccionar hotel..."
      getOptionLabel={(h) => h?.name}
      getOptionValue={(h) => h?.id}
      // Solo filtrar si NO es superusuario
      extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
    />
  )
}
```

### Ejemplo 2: Preseleccionar hotel si solo tiene uno

```jsx
import { useEffect } from 'react'
import { useFormikContext } from 'formik'
import { useUserHotels } from 'src/hooks/useUserHotels'

function ReservationForm() {
  const { setFieldValue } = useFormikContext()
  const { singleHotelId, hasSingleHotel } = useUserHotels()
  
  useEffect(() => {
    // Si el usuario solo tiene un hotel, preseleccionarlo automáticamente
    if (hasSingleHotel && singleHotelId) {
      setFieldValue('hotel', singleHotelId)
    }
  }, [hasSingleHotel, singleHotelId, setFieldValue])
  
  return (
    <SelectAsync
      title="Hotel *"
      name="hotel"
      resource="hotels"
      // ... resto de props
    />
  )
}
```

### Ejemplo 3: Mostrar selector solo si tiene múltiples hoteles

```jsx
import { useUserHotels } from 'src/hooks/useUserHotels'

function CreateRoomForm() {
  const { hasMultipleHotels, singleHotelId, hotelIdsString, isSuperuser } = useUserHotels()
  
  // Si es superuser o tiene múltiples hoteles, mostrar selector
  const showHotelSelector = isSuperuser || hasMultipleHotels
  
  return (
    <div>
      {showHotelSelector ? (
        <SelectAsync
          title="Hotel *"
          name="hotel"
          resource="hotels"
          extraParams={!isSuperuser && hotelIdsString ? { ids: hotelIdsString } : {}}
        />
      ) : (
        <>
          {/* Hotel oculto preseleccionado */}
          <input type="hidden" name="hotel" value={singleHotelId} />
          <p className="text-sm text-gray-600">
            Esta habitación se creará en tu hotel asignado.
          </p>
        </>
      )}
    </div>
  )
}
```

## 📊 Valores retornados

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `hotels` | `Array` | Array de objetos hotel `{id, name, city, timezone}` |
| `hotelIds` | `Array<number>` | Array de IDs de hoteles `[1, 2, 3]` |
| `hotelIdsString` | `string` | IDs separados por coma `"1,2,3"` |
| `hasMultipleHotels` | `boolean` | Si el usuario tiene más de un hotel |
| `hasSingleHotel` | `boolean` | Si el usuario tiene exactamente un hotel |
| `singleHotelId` | `number\|null` | ID del único hotel (si solo tiene uno) |
| `isSuperuser` | `boolean` | Si es superusuario (ve todos los hoteles) |

## 🔐 Lógica de permisos

- **Superusuarios (`is_superuser`)**: Ven todos los hoteles (no se aplica filtro)
- **Usuarios con perfil**: Solo ven sus hoteles asignados
- **Usuarios sin perfil**: No ven ningún hotel (array vacío)

## 🎯 Casos de uso comunes

1. **Filtrar hoteles en formularios de creación** (reservas, habitaciones, etc.)
2. **Preseleccionar hotel automáticamente** si el usuario solo tiene uno
3. **Ocultar selector de hotel** si solo tiene uno asignado
4. **Mostrar información contextual** sobre hoteles del usuario
5. **Validar permisos** antes de realizar acciones

## ⚙️ Backend

El backend filtra por IDs usando el parámetro `?ids=1,2,3`:

```
GET /api/hotels/?ids=1,2,3
```

Esto retorna solo los hoteles con IDs 1, 2 y 3.

