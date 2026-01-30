from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0012_backfill_room_base_currency_from_hotel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="base_currency",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="rooms_base",
                to="core.currency",
                help_text="Moneda de la tarifa principal",
            ),
        ),
    ]

