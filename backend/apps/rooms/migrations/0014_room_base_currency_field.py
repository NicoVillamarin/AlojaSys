from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_hotel_currency_swap"),
        ("rooms", "0011_room_secondary_price_currency"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="base_currency",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rooms_base",
                to="core.currency",
                help_text="Moneda de la tarifa principal",
            ),
        ),
    ]

