from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_remove_hotel_currency"),
        ("reservations", "0024_alter_reservation_channel"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="price_source",
            field=models.CharField(
                choices=[("primary", "Tarifa principal"), ("secondary", "Tarifa secundaria")],
                default="primary",
                help_text="Define si la reserva se cotiza/paga con tarifa principal o secundaria de la habitación",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="pricing_currency",
            field=models.ForeignKey(
                blank=True,
                help_text="Snapshot de moneda usada para cotizar/pagar la reserva",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reservations_priced",
                to="core.currency",
            ),
        ),
    ]

