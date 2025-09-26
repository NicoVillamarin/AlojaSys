from django.db import migrations


SQL_RENAME = r'''
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'core_enterprise'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'enterprises_enterprise'
    ) THEN
        ALTER TABLE public.core_enterprise RENAME TO enterprises_enterprise;
    END IF;
END $$;
'''


class Migration(migrations.Migration):

    dependencies = [
        ('enterprises', '0002_alter_enterprise_options'),
    ]

    operations = [
        migrations.RunSQL(SQL_RENAME),
    ]


