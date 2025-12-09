# Guía: Cómo Obtener un Número de WhatsApp Sandbox para Pruebas

## Requisitos Previos

1. **Cuenta de Facebook** (puede ser personal)
2. **Acceso a internet** para configurar la cuenta
3. **Número de teléfono** para verificación (puede ser el tuyo)

---

## Paso 1: Crear Cuenta en Meta for Developers

1. **Ir a Meta for Developers**:
   - Visita: https://developers.facebook.com/
   - Inicia sesión con tu cuenta de Facebook

2. **Crear una App**:
   - Haz clic en **"Mis Apps"** (arriba a la derecha)
   - Selecciona **"Crear App"**
   - Elige **"Negocio"** como tipo de app
   - Completa:
     - **Nombre de la app**: Ej. "AlojaSys WhatsApp Test"
     - **Email de contacto**: Tu email
     - **Propósito**: Selecciona "Administrar comunicaciones de negocio"
   - Haz clic en **"Crear App"**

---

## Paso 2: Agregar Producto WhatsApp

1. **En el Dashboard de tu App**:
   - Busca la sección **"Agregar productos a tu app"**
   - Encuentra **"WhatsApp"** y haz clic en **"Configurar"**

2. **Configurar WhatsApp Business API**:
   - Te llevará a la configuración de WhatsApp
   - Si es la primera vez, te pedirá aceptar términos y condiciones

---

## Paso 3: Obtener Número de Sandbox

1. **Ir a "API Setup"** (en el menú lateral izquierdo):
   - Verás una sección **"Step 1: Add a phone number"**
   - Haz clic en **"Add phone number"** o **"Agregar número de teléfono"**

2. **Número de Prueba (Sandbox)**:
   - Meta te asignará automáticamente un **número de prueba**
   - Este número tiene el formato: `+1 415 555 XXXX` (número ficticio)
   - **No necesitas un número real** para el sandbox

3. **Anotar el Número**:
   - Copia el número que te asignan (ejemplo: `+14155551234`)
   - Este es el número que usarás en AlojaSys

---

## Paso 4: Obtener Credenciales de API

1. **Phone Number ID**:
   - En la misma página de "API Setup"
   - Busca **"Phone number ID"**
   - Copia este ID (es un número largo, ej: `123456789012345`)

2. **Temporary Access Token**:
   - En la misma página, busca **"Temporary access token"**
   - Haz clic en **"Copy"** para copiar el token
   - ⚠️ **Importante**: Este token es temporal (válido por 24 horas)
   - Para producción necesitarás un token permanente (ver más abajo)

3. **Business Account ID** (opcional):
   - Si lo necesitas, está en la sección "Business Account"
   - Generalmente no es necesario para el sandbox básico

---

## Paso 5: Configurar en AlojaSys

1. **Ir a Configuración de Hoteles**:
   - En AlojaSys, ve a **Configuración → Hoteles**
   - Edita el hotel donde quieres probar WhatsApp

2. **Completar Campos de WhatsApp**:
   - **WhatsApp habilitado**: ✅ Activar
   - **Número de WhatsApp**: El número de sandbox (ej: `+14155551234`)
   - **Proveedor**: `meta_cloud`
   - **Phone Number ID**: El ID que copiaste
   - **API Token**: El token temporal que copiaste
   - **Business ID**: (opcional, dejar vacío si no lo tienes)

3. **Guardar** y probar

---

## Paso 6: Probar el Chatbot

### Opción A: Usar el CLI de Prueba

```bash
# Desde el directorio del proyecto
cd backend
python whatsapp_chat_cli.py
```

El script te pedirá:
- Tu número de teléfono (el que recibirá mensajes)
- El número del hotel (el de sandbox que configuraste)

### Opción B: Enviar Mensaje Manual desde Meta

1. **En Meta for Developers**:
   - Ve a **"API Setup"**
   - Busca la sección **"Send and receive messages"**
   - Ingresa tu número de teléfono personal (el que quieres usar para recibir)
   - Haz clic en **"Send message"**
   - Recibirás un código de verificación

2. **Verificar número**:
   - Ingresa el código que recibiste
   - Ahora puedes enviar mensajes desde el sandbox a tu número

---

## Limitaciones del Sandbox

⚠️ **Importante**: El sandbox tiene limitaciones:

1. **Solo puedes enviar mensajes a números verificados**:
   - Debes agregar números manualmente en Meta for Developers
   - No puedes recibir mensajes de números no verificados

2. **Token temporal**:
   - El token expira en 24 horas
   - Debes renovarlo manualmente desde Meta for Developers

3. **Número ficticio**:
   - El número de sandbox no es un número real de WhatsApp
   - No recibirás mensajes reales de clientes

---

## Solución de Problemas

### Error: "Este número no tiene WhatsApp configurado"

**Causa**: El número ingresado no coincide exactamente con el configurado.

**Solución**:
1. Verifica que el número en AlojaSys sea **exactamente igual** al de Meta
2. Incluye el código de país (ej: `+14155551234`, no `14155551234`)
3. No uses espacios ni guiones

### Error: "Token inválido"

**Causa**: El token expiró (son válidos por 24 horas).

**Solución**:
1. Ve a Meta for Developers → Tu App → WhatsApp → API Setup
2. Copia el nuevo **Temporary access token**
3. Actualiza el token en AlojaSys

### No recibo mensajes

**Causa**: Tu número no está verificado en el sandbox.

**Solución**:
1. Ve a Meta for Developers → API Setup
2. En "Send and receive messages", agrega tu número
3. Verifica el código que recibes

---

## Próximos Pasos: Producción

Para usar WhatsApp en producción, necesitarás:

1. **Número de WhatsApp Business verificado**:
   - A través de un proveedor oficial (Meta, Twilio, etc.)
   - O usando tu propio número si cumples requisitos

2. **Token permanente**:
   - Configurar un sistema de autenticación permanente
   - Usar tokens de larga duración o renovación automática

3. **Webhook público**:
   - Configurar una URL pública para recibir mensajes
   - Usar HTTPS con certificado válido

---

## Recursos Útiles

- **Documentación oficial de Meta**: https://developers.facebook.com/docs/whatsapp
- **Guía de inicio rápido**: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **API Reference**: https://developers.facebook.com/docs/whatsapp/cloud-api/reference

---

## Resumen Rápido

1. ✅ Crear cuenta en Meta for Developers
2. ✅ Crear una App de tipo "Negocio"
3. ✅ Agregar producto "WhatsApp"
4. ✅ Obtener número de sandbox y Phone Number ID
5. ✅ Copiar Temporary Access Token
6. ✅ Configurar en AlojaSys (Configuración → Hoteles)
7. ✅ Probar con `whatsapp_chat_cli.py`

---

**Nota**: Si tenés problemas para crear la cuenta en Meta, puede ser por:
- Restricciones de región
- Cuenta de Facebook nueva o sin verificar
- Problemas de cookies/caché del navegador

**Solución temporal**: Intentá desde otro navegador o dispositivo, o contactá con soporte de Meta.

