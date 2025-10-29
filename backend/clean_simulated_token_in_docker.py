"""
Script para limpiar tokens AFIP simulados directamente en la base de datos
Ejecuta este script desde fuera del contenedor Docker, conectándose a PostgreSQL
"""
import psycopg2
import os
from decouple import config

# Configuración de la base de datos desde .env
DB_NAME = config('POSTGRES_DB', default='hotel')
DB_USER = config('POSTGRES_USER', default='postgres')
DB_PASSWORD = config('POSTGRES_PASSWORD', default='postgres')
DB_HOST = config('POSTGRES_HOST', default='localhost')
DB_PORT = config('POSTGRES_PORT', default='5432')

def main():
    """Limpia tokens simulados en PostgreSQL"""
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # Buscar configuraciones con tokens simulados
        cur.execute("""
            SELECT id, afip_token, hotel_id, environment
            FROM invoicing_afipconfig
            WHERE afip_token LIKE 'SIMULATED_TOKEN_%'
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("✓ No se encontraron tokens simulados en la BD")
            conn.close()
            return
        
        print(f"Encontradas {len(rows)} configuración(es) con tokens simulados\n")
        
        # Limpiar cada token simulado
        for config_id, token, hotel_id, environment in rows:
            try:
                cur.execute("""
                    UPDATE invoicing_afipconfig
                    SET afip_token = '',
                        afip_sign = '',
                        afip_token_generation = NULL,
                        afip_token_expiration = NULL
                    WHERE id = %s
                """, (config_id,))
                
                print(f"✓ Limpiado AfipConfig #{config_id}")
                print(f"  Hotel ID: {hotel_id}, Ambiente: {environment}")
                print(f"  Token anterior: {token[:50]}...")
                print()
                
            except Exception as e:
                print(f"✗ Error limpiando AfipConfig #{config_id}: {str(e)}")
                print()
        
        # Confirmar cambios
        conn.commit()
        
        print(f"✓✓✓ Limpieza completada: {len(rows)} configuración(es)")
        print("   Ahora reinicia el contenedor backend y reintenta enviar la factura")
        
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"✗ Error conectándose a PostgreSQL: {str(e)}")
        print("\nVerifica que:")
        print("1. PostgreSQL está corriendo (docker-compose up db)")
        print("2. Las credenciales en .env son correctas")
        print("3. El puerto 5432 está accesible")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == '__main__':
    main()

