from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("enterprises", "0005_state_sync_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # Quitar db_table personalizado del estado (volver al default)
                migrations.AlterModelTable(
                    name="enterprise",
                    table=None,
                ),
                # Asegurar que las opciones de Meta coincidan con el modelo actual
                migrations.AlterModelOptions(
                    name="enterprise",
                    options={
                        "verbose_name": "Empresa",
                        "verbose_name_plural": "Empresas",
                    },
                ),
            ],
        ),
    ]


