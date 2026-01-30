from django.db import migrations


def forwards_backfill(apps, schema_editor):
    Room = apps.get_model("rooms", "Room")
    Currency = apps.get_model("core", "Currency")

    ars, _ = Currency.objects.get_or_create(code="ARS", defaults={"name": "ARS"})

    # Copiar moneda del hotel hacia room.base_currency (fallback ARS)
    # Usamos values para evitar problemas de imports.
    for room in Room.objects.select_related("hotel", "hotel__currency").all().only("id", "base_currency", "hotel"):
        if getattr(room, "base_currency_id", None):
            continue
        hotel = getattr(room, "hotel", None)
        curr = getattr(hotel, "currency", None) if hotel else None
        room.base_currency = curr or ars
        room.save(update_fields=["base_currency"])


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0014_room_base_currency_field"),
    ]

    operations = [
        migrations.RunPython(forwards_backfill, backwards_noop),
    ]

