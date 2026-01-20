# Módulo OTAs (Channel Manager) — Guía para Clientes

Este módulo permite que **AlojaSys** se conecte con **Booking.com / Airbnb / Expedia** a través de un **Channel Manager** (recomendado: **Smoobu**).

> Idea principal: **AlojaSys gestiona la operación** (reservas directas, check-in/out, cobros en el hotel, housekeeping) y **Smoobu gestiona la distribución** hacia OTAs (y recibe reservas de OTAs).

---

## ¿Qué resuelve este módulo?

- **Evita overbooking**: cuando se crea una reserva directa en AlojaSys, se bloquean automáticamente esas fechas en Smoobu y se reflejan en Booking/Airbnb.
- **Reservas entrantes automáticas**: cuando entra una reserva por Booking/Airbnb, llega a Smoobu y AlojaSys la registra automáticamente.
- **Trazabilidad**: las reservas OTAs se identifican en AlojaSys como **“Booking - Smoobu”**, **“Airbnb - Smoobu”**, etc.

---

## Cómo funciona (circuito simple)

### 1) Reservas que entran desde OTAs (Booking/Airbnb → Smoobu → AlojaSys)
- La reserva se crea en Booking/Airbnb.
- Smoobu la recibe.
- AlojaSys la importa automáticamente y la verás en tu lista/calendario de reservas.

**Notas importantes**
- Puede haber **demora** (normal) entre Booking y Smoobu en algunos casos.
- El estado en Booking puede pasar por “pendiente/solicitud” y recién luego aparecer como reserva firme en Smoobu/AlojaSys.

### 2) Reservas directas creadas en AlojaSys (AlojaSys → Smoobu → Booking/Airbnb)
- Cuando creás una reserva directa en AlojaSys, AlojaSys envía un **bloqueo** a Smoobu.
- Smoobu replica ese bloqueo a Booking/Airbnb para cerrar disponibilidad.

**Aclaración**
- En Booking/Airbnb **no vas a ver una “reserva” creada por AlojaSys**.  
  Vas a ver **fechas cerradas/no disponibles** (bloqueo), que es el comportamiento correcto.

---

## Tarifas y precios (recomendación para evitar problemas)

Para que sea simple y estable:

- **Tarifas OTAs** (Booking/Airbnb/Expedia): se gestionan en **Smoobu**.
- **Tarifa directa** (venta directa, mostrador, WhatsApp): se gestiona en **AlojaSys**.

Esto evita “guerra de precios” y diferencias de totales entre sistemas.

En AlojaSys vas a ver:
- **Precio (AlojaSys)**: editable, aplica a reservas directas.
- **Precio OTA (Smoobu)**: **solo lectura**, se gestiona en Smoobu.

---

## Cancelaciones (regla simple)

- **Reservas OTAs**: se cancelan en **Booking/Airbnb/Smoobu**.  
  AlojaSys se actualiza automáticamente cuando llega la cancelación.
- **Reservas directas**: se cancelan en **AlojaSys**.

---

## Emails de huéspedes (Booking y privacidad)

Booking muchas veces entrega un email tipo:
`nombre.apellido.123456@guest.booking.com`

Eso es un **alias de privacidad de Booking**: no es un “error”.  
Sirve para contactar al huésped **a través de Booking** (Booking redirige el mensaje).

---

## Configuración (paso a paso)

### A) En Smoobu
1. Contratar Smoobu.
2. Conectar los canales (Booking / Airbnb / etc.).
3. Obtener la **API Key** de Smoobu.
4. Configurar el **Webhook** de AlojaSys en Smoobu (la URL la provee el equipo de AlojaSys).

### B) En AlojaSys
En **Configuración → OTAs**:
1. Crear/editar proveedor **Smoobu**:
   - Cargar la **API Key**.
2. Mapear habitaciones:
   - Por cada habitación/unidad en AlojaSys, cargar el **Smoobu Apartment ID** correspondiente.
3. Verificar que el mapeo quede **Activo**.

> Si una habitación no está mapeada, AlojaSys no puede importar/exportar correctamente para esa unidad.

---

## Checklist rápido de “está funcionando”

- **Reserva de Booking** → aparece en Smoobu → aparece en AlojaSys.
- **Reserva directa en AlojaSys** → en Smoobu aparece un **bloqueo** → en Booking/Airbnb se ve el calendario cerrado.
- En AlojaSys, las reservas de OTAs aparecen con canal **“X - Smoobu”**.

---

## Problemas comunes (y qué significa)

- **No aparece una reserva en AlojaSys**:
  - Puede ser **demora** entre Booking y Smoobu.
  - Puede faltar el **mapeo** (Apartment ID) de esa unidad.

- **No se bloquean fechas cuando creo una reserva directa**:
  - Falta configuración de Smoobu (API Key) o el mapeo del Apartment ID.
  - El equipo técnico puede validar logs y configuración del sync.

- **Veo datos raros del huésped (email @guest.booking.com)**:
  - Es normal por política de privacidad de Booking.

---

## Qué información necesitamos para ayudarte rápido (soporte)

Cuando reportes un problema, envianos:
- Hotel y habitación/unidad.
- Fecha de check-in / check-out.
- Si es OTA: número de reserva de Booking/Airbnb (si lo tenés).
- Captura del mapeo (Apartment ID) en AlojaSys.
- (Opcional) captura del booking en Smoobu.

