from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("housekeeping", "0007_add_task_duration_and_overdue"),
    ]

    operations = [
        migrations.AddField(
            model_name="housekeepingconfig",
            name="daily_for_all_rooms",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activo, genera tareas diarias para todas las habitaciones activas "
                    "del hotel (no solo ocupadas)."
                ),
            ),
        ),
    ]


