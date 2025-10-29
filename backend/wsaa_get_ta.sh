#!/bin/sh
set -e

# Lee rutas CERT/KEY desde AfipConfig
CERT_PATH=$(python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","hotel.settings")
django.setup()
from apps.invoicing.models import AfipConfig
c = AfipConfig.objects.first()
print(c.certificate_path)
PY
)

KEY_PATH=$(python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","hotel.settings")
django.setup()
from apps.invoicing.models import AfipConfig
c = AfipConfig.objects.first()
print(c.private_key_path)
PY
)

cd /app

# 1) TRA con ventana ?10m y uniqueId din?mico
UNIQ=$(date +%s)
GEN="$(date -d "-10 minutes" +"%Y-%m-%dT%H:%M:%S%:z")"
EXP="$(date -d "+10 minutes" +"%Y-%m-%dT%H:%M:%S%:z")"

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

# 2) Firmar CMS (DER)
openssl smime -sign -in TRA.xml -signer "$CERT_PATH" -inkey "$KEY_PATH" -out TRA.cms -outform DER -nodetach -binary

# 3) SOAP y POST a WSAA
CMS=$(base64 TRA.cms)
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
  -H "Content-Type: text/xml; charset=utf-8" -H "SOAPAction: urn:LoginCms" \
  --data @login.xml > wsaa_resp.xml || true

echo "faultstring:"
xmlstarlet sel -t -v "string(//faultstring)" -n wsaa_resp.xml || true

# 4) Extraer loginCmsReturn
RET=$(xmlstarlet sel -t -v "string(//loginCmsReturn)" wsaa_resp.xml 2>/dev/null || true)
[ -z "$RET" ] && echo "NO_LOGIN_RETURN" && head -n 60 wsaa_resp.xml && exit 1

# 5) Decodificar (base64) o des-escapar si viene como XML escapado
echo "$RET" > LTR.raw
if base64 -d LTR.raw > LTR.xml 2>/dev/null; then
  : # ok
else
  python - <<'PY'
import html
raw = open('LTR.raw','r',encoding='utf-8',errors='ignore').read()
unesc = html.unescape(raw)
open('LTR.xml','w',encoding='utf-8').write(unesc)
PY
fi

# 6) Obtener token/sign
TOKEN=$(xmlstarlet sel -t -v "string(//token)" LTR.xml 2>/dev/null || true)
SIGN=$(xmlstarlet sel -t -v "string(//sign)"  LTR.xml 2>/dev/null || true)
echo "TOKEN_PREVIEW=${TOKEN:0:40}..."
echo "SIGN_PREVIEW=${SIGN:0:40}..."
[ -z "$TOKEN" -o -z "$SIGN" ] && echo "MISSING_TOKEN_OR_SIGN" && exit 1

# 7) Inyectar en BD
python - <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","hotel.settings")
django.setup()
from apps.invoicing.models import AfipConfig
from django.utils import timezone
from xml.etree import ElementTree as ET

cfg = AfipConfig.objects.first()
root = ET.parse('LTR.xml').getroot()
cfg.afip_token = root.findtext('.//token')
cfg.afip_sign  = root.findtext('.//sign')
cfg.afip_token_generation = timezone.now()
cfg.afip_token_expiration = timezone.now() + timezone.timedelta(hours=12)
cfg.save(update_fields=['afip_token','afip_sign','afip_token_generation','afip_token_expiration'])
print('INJECTED_OK')
PY

echo "DONE"
