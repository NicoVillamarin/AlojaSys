# Configuración de Certificados AFIP para AlojaSys

## 🎯 Objetivo
Configurar certificados digitales válidos para conectarse a AFIP homologación y probar el circuito completo de facturación electrónica.

## 📋 Proceso Completo

### 1. Generar CSR (Certificate Signing Request)
```bash
python certs/generate_afip_certificates.py
```

Esto genera:
- `certs/afip_private_key.key` - Clave privada
- `certs/afip_certificate_request.csr` - Solicitud de certificado

### 2. Obtener Certificado de AFIP

#### 2.1 Acceder a AFIP
1. Ve a https://www.afip.gob.ar
2. Inicia sesión con tu Clave Fiscal

#### 2.2 Adherir al servicio WSASS
1. Ve a "Administrador de Relaciones de Clave Fiscal"
2. Adhiere al servicio "WSASS - Autogestión Certificados Homologación"

#### 2.3 Crear certificado
1. Ve a WSASS > "Nuevo Certificado"
2. Nombre simbólico: `AlojaSys Test System`
3. Copia el contenido completo de `certs/afip_certificate_request.csr`:

```
-----BEGIN CERTIFICATE REQUEST-----
MIICpDCCAYwCAQAwXzELMAkGA1UEBhMCQVIxFjAUBgNVBAoMDUFsb2phU3lzIFRl
c3QxHTAbBgNVBAMMFEFsb2phU3lzIFRlc3QgU3lzdGVtMRkwFwYDVQQFExBDVUlU
IDIwMTIzNDU2Nzg5MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1b4z
O0STETcyOYev8FX47AGMoD43JUY6lIHSGcQqV9slbXtpPXthwmuaW9rWTWandhYP
emWUsT0vyiJm+UHU2DRh+gHoWai8K7Si0gy5br47tAX4lHCrgmBDdpqTlNm/HuMa
WEU5YM4jpMwW/MP3c11a5iSNbzeICvok9k2VljZ6a8OkNM/BZQPywAQYB76c2vkG
w21jsuCALbQ1wtmhcjXhNCmYZOV5jb1wrU4deqSFYMAuLjKobY1TnDjzoRICjsRd
NZJEMqcCiNlFpKQVj4Oxynufo20UPv52e38zJ809r9JmBcqTwhvpcCsB9nPx1FrL
2sW19iWB9igHVcTHLQIDAQABoAAwDQYJKoZIhvcNAQELBQADggEBAGFUbOGGeIkD
FUzBMLWTChgzGiW5y4A3KIo8UKn70bhy0YtCavnDPCZxjaBrrSCl+EqepdbyqdEv
ysrLQnasXusqQ+6E9pBYgkgV+bJ9E86VlmheJNjI8LiiBOnGRxje3J+sHHk5fujE
TKR+RvOVsk/aZPScceNZb6NpUitwyvVs7AmhIpGPfDPN4Io2z9+gOGClD3e2JHnl
ulw3qzhPaRo6017PscBBzopXavLwH89WnDMLtvfTcZrLWkYhlyWzGyuBBxIiNaWa
l4qPR2XmnasyFPOAXTToP3NnlWL2a29AREFcBdnPKG2W/uK2fKHgvftRneYORnZA
kkh0Us1Tbak=
-----END CERTIFICATE REQUEST-----
```

4. Pega el contenido en el campo "Solicitud del certificado"
5. Haz clic en "Crear DN y obtener certificado"

#### 2.4 Descargar certificado
1. Copia el certificado generado por AFIP
2. Guárdalo como `certs/afip_certificate.crt`

#### 2.5 Autorizar certificado
1. Ve a "Administrador de Relaciones de Clave Fiscal"
2. Adhiere al servicio "Facturación Electrónica"
3. Selecciona tu certificado como representante

### 3. Configurar en el Sistema
```bash
python certs/setup_afip_real.py
```

Esto:
- Copia los certificados al contenedor Docker
- Actualiza la configuración en la base de datos
- Configura las rutas correctas

### 4. Configurar en el Frontend

En el modal "Editar Configuración ARCA", usa estas rutas:

```
Ruta del Certificado (.crt): /app/certs/afip_certificate.crt
Ruta de la Clave Privada (.key): /app/certs/afip_private_key.key
```

### 5. Probar Conexión

Una vez configurado, prueba la conexión desde el frontend. Debería conectarse exitosamente a AFIP homologación.

## 🧪 Endpoints de Prueba

- `GET /api/invoicing/test/certificates/validate/` - Validar certificados
- `POST /api/invoicing/test/afip/connection/` - Probar conexión AFIP
- `POST /api/invoicing/test/invoices/generate/` - Generar factura de prueba
- `GET /api/invoicing/test/afip/status/` - Estado general de AFIP

## ⚠️ Notas Importantes

1. **Certificados de Prueba**: Los certificados generados son para homologación (testing) únicamente
2. **No Producción**: No uses estos certificados en producción
3. **Vigencia**: Los certificados de AFIP tienen vigencia limitada
4. **Renovación**: Debes renovar los certificados cuando expiren

## 🔧 Troubleshooting

### Error: "Certificado no encontrado"
- Verifica que los archivos estén en el contenedor Docker
- Ejecuta: `docker exec hotel_backend ls -la /app/certs/`

### Error: "Error de autenticación AFIP"
- Verifica que el certificado esté autorizado para "Facturación Electrónica"
- Verifica que las URLs de AFIP sean correctas

### Error: "404 Not Found"
- Verifica que estés usando las URLs de homologación, no producción
- Verifica que el servicio WSASS esté habilitado en tu cuenta AFIP


