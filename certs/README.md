# Certificados de Prueba para AFIP

Este directorio contiene los certificados digitales generados para pruebas con AFIP.

## Archivos Generados

- `test_private_key.key` - Clave privada RSA
- `test_certificate.crt` - Certificado autofirmado
- `test_certificate_request.csr` - Solicitud de certificado (CSR)
- `test_certificate.pfx` - Certificado en formato PFX
- `test_config.py` - Configuración de prueba

## Uso

### 1. Configuración en Django

```python
# En tu configuración de AFIP
AFIP_CONFIG = {
    'certificate_path': 'certs/test_certificate.crt',
    'private_key_path': 'certs/test_private_key.key',
    'environment': 'test',
    'cuit': '20123456789',
    'point_of_sale': 1
}
```

### 2. Configuración en el Modelo

```python
from apps.invoicing.models import AfipConfig

# Crear configuración de prueba
config = AfipConfig.objects.create(
    hotel=hotel,
    cuit='20123456789',
    point_of_sale=1,
    certificate_path='certs/test_certificate.crt',
    private_key_path='certs/test_private_key.key',
    environment='test'
)
```

## Importante

⚠️ **ESTOS CERTIFICADOS SON SOLO PARA PRUEBAS**

- NO uses estos certificados en producción
- Para producción, obtén certificados reales de AFIP
- Estos certificados son autofirmados y no son válidos para AFIP real

## Regenerar Certificados

Para regenerar los certificados, ejecuta:

```bash
python certs/generate_certificates_python.py
```

## Próximos Pasos

1. Configura estos certificados en tu sistema AFIP
2. Usa las rutas en tu configuración de Django
3. Prueba la conexión con AFIP homologación
4. Para producción, obtén certificados reales de AFIP
