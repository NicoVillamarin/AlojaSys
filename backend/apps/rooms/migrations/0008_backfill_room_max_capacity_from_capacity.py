from django.db import migrations, models


def forwards(apps, schema_editor):
    Room = apps.get_model("rooms", "Room")
    # Si max_capacity quedó por defecto (o menor), lo alineamos a capacity.
    Room.objects.filter(max_capacity__lt=models.F("capacity")).update(
        max_capacity=models.F("capacity")
    )


def backwards(apps, schema_editor):
    # No es reversible de forma segura (no sabemos el valor anterior).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("rooms", "0007_room_cleaning_status_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]


