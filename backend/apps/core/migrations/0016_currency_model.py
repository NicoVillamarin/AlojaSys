from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_hotel_currency"),
    ]

    operations = [
        migrations.CreateModel(
            name="Currency",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=10, unique=True)),
                ("name", models.CharField(blank=True, max_length=80)),
                ("symbol", models.CharField(blank=True, max_length=10)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Moneda",
                "verbose_name_plural": "Monedas",
                "ordering": ["code"],
            },
        ),
    ]

