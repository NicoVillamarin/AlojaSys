#!/bin/sh
set -e
cd /app

# Tiempos (ventana ?10m) y uniqueId din?mico
UNIQ=$(date +%s)
GEN="$(date -u -d "-10 minutes" +"%Y-%m-%dT%H:%M:%S")-03:00"
EXP="$(date -u -d "+10 minutes" +"%Y-%m-%dT%H:%M:%S")-03:00"

cat > TRA.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
  <header>
    <uniqueId>$UNIQ</uniqueId>
    <generationTime>$GEN</generationTime>
    <expirationTime>$EXP</expirationTime>
  </header>
  <service>wsfe</service>
</loginTicketRequest>
EOF

# CMS PKCS#7 DER
openssl smime -sign -in TRA.xml \
  -signer /app/certs/afip_certificate_20375572304.crt \
  -inkey /app/certs/afip_private_key_20375572304.key \
  -out TRA.cms -outform DER -nodetach -binary

CMS=$(base64 TRA.cms)

# SOAP con SOAPAction correcto
cat > login.xml << EOF
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsaa="http://wsaa.view.sua.dvad.gov.ar/">
  <soapenv:Header/>
  <soapenv:Body>
    <wsaa:loginCms>
      <wsaa:in0>$CMS</wsaa:in0>
    </wsaa:loginCms>
  </soapenv:Body>
</soapenv:Envelope>
EOF

curl -s --http1.1 -X POST "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" \
  -H "Content-Type: text/xml; charset=utf-8" \
  -H "SOAPAction: urn:LoginCms" \
  --data @login.xml > wsaa_resp.xml || true

echo "----- faultstring (si existe) -----"
xmlstarlet sel -t -v "string(//faultstring)" -n wsaa_resp.xml || true

RET=$(xmlstarlet sel -t -v "string(//loginCmsReturn)" wsaa_resp.xml 2>/dev/null || true)
if [ -z "$RET" ]; then
  echo "NO_LOGIN_RETURN"
  head -n 80 wsaa_resp.xml || true
  exit 1
fi

echo "$RET" > LTR.b64
if ! base64 -d LTR.b64 > LTR.xml 2>/dev/null; then
  echo "RETURN_NO_BASE64"
  exit 1
fi

TOKEN=$(xmlstarlet sel -t -v "string(//token)" LTR.xml 2>/dev/null || true)
SIGN=$(xmlstarlet sel -t -v "string(//sign)" LTR.xml 2>/dev/null || true)

echo "TOKEN_PREVIEW=${TOKEN:0:60}..."
echo "SIGN_PREVIEW=${SIGN:0:60}..."

if [ -z "$TOKEN" ] || [ -z "$SIGN" ]; then
  echo "MISSING_TOKEN_OR_SIGN"
  exit 1
fi

python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','hotel.settings')
django.setup()
from apps.invoicing.models import AfipConfig
from django.utils import timezone
from xml.etree import ElementTree as ET

config = AfipConfig.objects.first()
if not config:
    print('NO_CONFIG'); raise SystemExit(1)

root = ET.parse('LTR.xml').getroot()
token = root.findtext('.//token')
sign  = root.findtext('.//sign')
if not token or not sign:
    print('NO_TA_VALUES'); raise SystemExit(1)

config.afip_token = token
config.afip_sign = sign
config.afip_token_generation = timezone.now()
config.afip_token_expiration = timezone.now() + timezone.timedelta(hours=12)
config.save(update_fields=['afip_token','afip_sign','afip_token_generation','afip_token_expiration'])
print('INJECTED_OK')
PY

echo "DONE"
