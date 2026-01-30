from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0021_update_receipt_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="refund",
            name="currency",
            field=models.CharField(
                default="ARS",
                help_text="Código de moneda del reembolso (ISO 4217, ej. ARS, USD)",
                max_length=10,
            ),
        ),
    ]

