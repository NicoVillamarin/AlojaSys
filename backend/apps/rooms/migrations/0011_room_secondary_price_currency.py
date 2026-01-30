from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_hotel_currency_swap"),
        ("rooms", "0010_room_amenities"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="secondary_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="room",
            name="secondary_currency",
            field=models.ForeignKey(
                blank=True,
                help_text="Moneda de la tarifa secundaria",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rooms_secondary",
                to="core.currency",
            ),
        ),
    ]

