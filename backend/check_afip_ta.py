"""
Script para verificar si hay TA guardado en AfipConfig
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
    
    cur.execute("""
        SELECT id, hotel_id, afip_token, afip_sign, afip_token_generation, afip_token_expiration
        FROM invoicing_afipconfig
        LIMIT 1
    """)
    
    row = cur.fetchone()
    
    if row:
        config_id, hotel_id, token, sign, gen, exp = row
        print(f"✓ AfipConfig encontrado:")
        print(f"  ID: {config_id}")
        print(f"  Hotel ID: {hotel_id}")
        print(f"  Token: {token[:60] if token else 'VACIO'}...")
        print(f"  Sign: {sign[:40] if sign else 'VACIO'}...")
        print(f"  Generation: {gen}")
        print(f"  Expiration: {exp}")
    else:
        print("✗ No hay AfipConfig en la BD")
    
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")

