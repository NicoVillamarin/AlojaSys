"""
Script para verificar configuración AFIP completa en la BD
"""
import psycopg2
from decouple import config

DB_NAME = config('POSTGRES_DB', default='hotel')
DB_USER = config('POSTGRES_USER', default='postgres')
DB_PASSWORD = config('POSTGRES_PASSWORD', default='postgres')
DB_HOST = config('POSTGRES_HOST', default='localhost')
DB_PORT = config('POSTGRES_PORT', default='5432')

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    # Obtener toda la info de AfipConfig
    cur.execute("""
        SELECT id, hotel_id, cuit, point_of_sale, certificate_path, private_key_path,
               environment, afip_token, afip_sign, afip_token_generation, afip_token_expiration,
               is_active, created_at, updated_at
        FROM invoicing_afipconfig
        LIMIT 1
    """)
    
    row = cur.fetchone()
    
    if row:
        print("=" * 80)
        print("CONFIGURACION AFIP COMPLETA:")
        print("=" * 80)
        print(f"ID: {row[0]}")
        print(f"Hotel ID: {row[1]}")
        print(f"CUIT: {row[2]}")
        print(f"Punto de Venta: {row[3]}")
        print(f"Certificado: {row[4]}")
        print(f"Clave Privada: {row[5]}")
        print(f"Ambiente: {row[6]}")
        print(f"\nTOKEN:")
        print(f"  Valor: {row[7][:60] if row[7] else 'VACIO'}...")
        print(f"  Generation: {row[8]}")
        print(f"  Expiration: {row[9]}")
        print(f"\nSIGN:")
        print(f"  Valor: {row[8][:60] if row[8] else 'VACIO'}...")
        print(f"\nEstado: {'Activo' if row[10] else 'Inactivo'}")
        print(f"Creado: {row[11]}")
        print(f"Actualizado: {row[12]}")
        print("=" * 80)
    else:
        print("✗ No hay AfipConfig en la BD")
    
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")

