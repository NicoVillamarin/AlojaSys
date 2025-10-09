## Módulo de Transacciones (Pagos)

Guía para que cada hotel/cliente configure y utilice pagos online con su propia cuenta de Mercado Pago, de forma segura y en modo prueba o producción.

### 1) Conceptos clave
- **Cuenta propia**: cada hotel usa sus credenciales de Mercado Pago. El sistema no cobra por vos ni mezcla fondos entre hoteles.
- **Modos**:
  - **Test**: no mueve dinero real. Ideal para pruebas y capacitación.
  - **Producción**: cobros reales al huésped.
- **Productos soportados**:
  - Checkout Bricks (pago en un modal dentro del sistema)
  - Checkout Pro (link/redirección de pago)

### 2) Requisitos del cliente (hotel)
1. Cuenta activa de Mercado Pago en su país.
2. Acceso al panel de Desarrolladores de Mercado Pago.
3. Credenciales de la aplicación (Public Key y Access Token) en modo Test y luego en modo Producción.

### 3) Obtener credenciales en Mercado Pago
1. Ingresar a Mercado Pago → Desarrolladores → Tus integraciones → Crear aplicación.
2. Completar:
   - Tipo de solución: Pagos online
   - Plataforma e‑commerce: No
   - Producto: Checkout Bricks (también sirve para Checkout Pro más adelante)
3. En la aplicación creada, ir a “Credenciales” y copiar:
   - **Public Key** (TEST‑… para pruebas / PROD‑… para producción)
   - **Access Token** (TEST‑… / PROD‑…)

Nota: La Public Key puede mostrarse en el frontend. El Access Token es privado (servidor) y nunca debe compartirse fuera de quien administre el sistema.

### 4) Cargar credenciales en el sistema (por hotel)
Ubicación: Panel de administración (Django Admin) → Pagos → Configuración de pasarela.

Crear una nueva configuración y completar:
- **Proveedor**: Mercado Pago
- **Hotel**: seleccionar el hotel (si gestiona varios, puede definir una por hotel)
- **Public Key**: pegar la clave correspondiente (TEST para pruebas)
- **Access Token**: pegar la clave correspondiente (TEST para pruebas)
- **Modo prueba (is_test)**: activado durante pruebas; desactivarlo al pasar a producción
- **Moneda (currency_code)**: código ISO del país (p. ej. ARS, BRL, CLP)
- **País (country_code)**: código ISO de 2 letras (p. ej. AR, BR, CL) — opcional si ya está definido en el hotel
- **Webhook secret**: cadena larga/única para validar notificaciones (puede ser cualquiera, mantenerla privada)
- **Activo**: habilitado

Sugerencia: si administra una cadena, también puede configurar a nivel Empresa y usarla como valor por defecto, con overrides por Hotel cuando sea necesario.

### 5) Flujo de cobro en el sistema
- Botón “Confirmar y pagar” en la reserva:
  - Si la tarifa del hotel requiere **seña/adelanto**: se cobra el depósito ahora y el saldo en el check‑in.
  - Si la tarifa requiere **pago total**: se cobra el 100% ahora.
- Métodos de pago disponibles:
  - **Checkout Bricks**: abre un modal y el huésped ingresa tarjeta/medios locales.
  - **Checkout Pro (opcional)**: se genera un link para pagar en otra pestaña; útil para “pagar más tarde”.
- Estados de la reserva:
  - Pendiente de pago → Confirmada (cuando Mercado Pago notifica “approved”).
  - Si hubo seña: queda “confirmada con saldo pendiente” para completar en recepción.

Importante: la confirmación final se hace con notificación de Mercado Pago (webhook) y verificación del pago en el servidor; no se depende del navegador del huésped.

### 6) Pasar de pruebas a producción
1. Verificar cobros en **modo Test** (simular pagos y revisar que cambie el estado de reservas).
2. En Mercado Pago, obtener **Public Key** y **Access Token** de **Producción**.
3. En el Admin, duplicar o editar la Configuración de pasarela del hotel y:
   - Reemplazar credenciales por las de Producción.
   - Desmarcar “is_test”.
4. Realizar una compra real pequeña para validar el circuito.

### 7) Seguridad y buenas prácticas
- Mantener el **Access Token** en el servidor. No compartirlo por email/chat.
- Usar **Webhook secret** y mantenerlo privado.
- El sistema verifica con Mercado Pago el estado/monto/moneda de cada pago antes de confirmar.
- Si las credenciales se filtran, rotarlas desde el panel de Mercado Pago y actualizarlas en el sistema.
- Recomienda a cada hotel usar una **cuenta empresarial** separada para producción.

### 8) Preguntas frecuentes
- ¿Puedo usar la misma aplicación de Mercado Pago para varios hoteles?  
  Sí, pero cada hotel debe cargar sus propias credenciales (de su propia cuenta) en el sistema para que el dinero ingrese a su cuenta.

- ¿Las comisiones quién las paga?  
  Mercado Pago descuenta su comisión del cobro. El hotel decide si la traslada o no al huésped (ver políticas locales).

- ¿Qué pasa si el huésped no completa el pago?  
  La reserva queda pendiente por un tiempo definido y puede liberarse si no se acredita.

- ¿Se pueden hacer reembolsos?  
  Sí, desde Mercado Pago; y el sistema puede reflejarlo (si está habilitado en la operativa del hotel).

### 9) Checklist de activación rápida (por hotel)
1. Crear aplicación en Mercado Pago y obtener credenciales (TEST y PROD).
2. Cargar en Admin → Pagos → Configuración de pasarela para el hotel.
3. Probar en modo Test (simular pago) y verificar cambio de estado de la reserva.
4. Pasar a Producción (reemplazar credenciales y desactivar “is_test”).
5. Realizar una compra real pequeña y validar.

### 10) Soporte
Si necesita ayuda para configurar sus credenciales o validar un pago, contacte al soporte del sistema indicando:
- Hotel, fecha y hora del intento de pago
- ID de la reserva
- Email del huésped
- Capturas de pantalla (si es posible)


