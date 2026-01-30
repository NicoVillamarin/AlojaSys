from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0013_room_base_currency_not_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="amenities_quantities",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Cantidades por amenity (dict: code -> int). Útil para camas (x2, x3, etc.)",
            ),
        ),
    ]

