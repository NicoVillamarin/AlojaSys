from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_hotel_guest_card_policies"),
    ]

    operations = [
        migrations.AddField(
            model_name="hotel",
            name="currency",
            field=models.CharField(
                max_length=3,
                default="ARS",
                help_text="Moneda principal de trabajo del hotel (ISO 4217, ej. ARS, USD, EUR)",
            ),
            preserve_default=True,
        ),
    ]

