# Módulo: OTAs (Channel Manager) — Guía para Clientes

Este módulo permite que **AlojaSys** se conecte con **Booking.com / Airbnb / Expedia** a través de un **Channel Manager** (recomendado: **Smoobu**).

> Idea principal: **AlojaSys gestiona la operación** (reservas directas, check-in/out, cobros en el hotel, housekeeping) y **Smoobu gestiona la distribución** hacia OTAs (y recibe reservas de OTAs).

## ¿Qué resuelve este módulo?

- **Evita overbooking**: reservas directas en AlojaSys bloquean fechas en Smoobu y se reflejan en OTAs.
- **Reservas entrantes automáticas**: reservas de Booking/Airbnb llegan a Smoobu y luego a AlojaSys.
- **Trazabilidad**: AlojaSys identifica el canal (ej: “Booking - Smoobu”).

## Cómo funciona (circuito simple)

### 1) Reservas que entran desde OTAs (Booking/Airbnb → Smoobu → AlojaSys)
- Se crea la reserva en la OTA.
- Smoobu la recibe.
- AlojaSys la importa y la verás en el sistema.

**Notas**
- Puede haber **demora** entre Booking y Smoobu en algunos casos.
- En Booking puede existir estado “pendiente/solicitud” previo a que llegue a Smoobu/AlojaSys.

### 2) Reservas directas creadas en AlojaSys (AlojaSys → Smoobu → OTAs)
- Cuando creás una reserva directa en AlojaSys, AlojaSys envía un **bloqueo** a Smoobu.
- Smoobu replica ese bloqueo a Booking/Airbnb para cerrar disponibilidad.

## Tarifas y precios (recomendación para evitar problemas)

- **Tarifas OTAs**: gestionarlas en **Smoobu**.
- **Tarifa directa**: gestionarla en **AlojaSys**.

Así evitás diferencias de totales entre sistemas.

## Cancelaciones (regla simple)

- **Reservas OTAs**: se cancelan en Booking/Airbnb/Smoobu (AlojaSys se actualiza al sincronizar).
- **Reservas directas**: se cancelan en AlojaSys.

## Emails de huéspedes (Booking y privacidad)

Booking puede mostrar emails como:
`nombre.apellido.123456@guest.booking.com`

Es un **alias de privacidad** (Booking redirige el mensaje).

## Configuración (paso a paso)

### En Smoobu
1. Conectar canales (Booking/Airbnb/etc.).
2. Obtener **API Key**.
3. Configurar **Webhook** (URL provista por AlojaSys).

### En AlojaSys
1. Ir a **Configuración → OTAs** y cargar la **API Key** de Smoobu.
2. Mapear habitaciones con el **Smoobu Apartment ID**.
3. Verificar que el mapeo quede **Activo**.

## Checklist rápido

- Reserva en Booking → aparece en Smoobu → aparece en AlojaSys.
- Reserva directa en AlojaSys → aparece como bloqueo en Smoobu → calendario cerrado en Booking/Airbnb.

