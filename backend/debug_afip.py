#!/usr/bin/env python3
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel.settings')
django.setup()

from apps.invoicing.models import AfipConfig
from apps.invoicing.services.afip_auth_service import AfipAuthService
import requests

try:
    config = AfipConfig.objects.get(hotel_id=1)
    auth = AfipAuthService(config)
    
    # Crear el XML de login
    login_xml = auth._create_login_xml()
    signed_xml = auth._sign_xml(login_xml)
    
    print('XML firmado creado correctamente')
    print('Longitud del XML:', len(signed_xml))
    
    # Enviar a AFIP
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'urn:LoginCms'
    }
    
    soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wsaa="{auth.WSAA_SOAP_NS}">
    <soapenv:Header/>
    <soapenv:Body>
        <wsaa:loginCms>
            <wsaa:in0>{signed_xml}</wsaa:in0>
        </wsaa:loginCms>
    </soapenv:Body>
</soapenv:Envelope>'''
    
    print('Enviando a:', auth.wsaa_url)
    response = requests.post(auth.wsaa_url, data=soap_body, headers=headers, timeout=30)
    
    print('Status code:', response.status_code)
    print('Content-Type:', response.headers.get('content-type', 'No content-type'))
    print('Primeros 1000 caracteres de respuesta:')
    print(response.text[:1000])
    print('...')
    print('Últimos 500 caracteres de respuesta:')
    print(response.text[-500:])
    
except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()
