from django.db import migrations


SQL_CREATE = r'''
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'enterprises_enterprise'
    ) THEN
        CREATE TABLE public.enterprises_enterprise (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(150) NOT NULL UNIQUE,
            legal_name VARCHAR(200) NOT NULL DEFAULT '',
            tax_id VARCHAR(50) NOT NULL DEFAULT '',
            email VARCHAR(254) NOT NULL DEFAULT '',
            phone VARCHAR(50) NOT NULL DEFAULT '',
            address VARCHAR(200) NOT NULL DEFAULT '',
            country_id BIGINT NULL,
            state_id BIGINT NULL,
            city_id BIGINT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        -- Añadir FKs si las tablas de locations existen
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='locations_country' AND table_schema='public') THEN
            ALTER TABLE public.enterprises_enterprise
                ADD CONSTRAINT enterprises_enterprise_country_fk FOREIGN KEY (country_id)
                REFERENCES public.locations_country(id) DEFERRABLE INITIALLY DEFERRED;
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='locations_state' AND table_schema='public') THEN
            ALTER TABLE public.enterprises_enterprise
                ADD CONSTRAINT enterprises_enterprise_state_fk FOREIGN KEY (state_id)
                REFERENCES public.locations_state(id) DEFERRABLE INITIALLY DEFERRED;
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='locations_city' AND table_schema='public') THEN
            ALTER TABLE public.enterprises_enterprise
                ADD CONSTRAINT enterprises_enterprise_city_fk FOREIGN KEY (city_id)
                REFERENCES public.locations_city(id) DEFERRABLE INITIALLY DEFERRED;
        END IF;
    END IF;
END $$;
'''


def forwards(apps, schema_editor):
    # Ejecutar solo en PostgreSQL; en SQLite no existe DO $$ ... $$
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(SQL_CREATE)


class Migration(migrations.Migration):

    dependencies = [
        ('enterprises', '0003_rename_core_to_default'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]


