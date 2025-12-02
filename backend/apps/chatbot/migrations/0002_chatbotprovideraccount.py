from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatbotProviderAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="Nombre interno de la cuenta/proveedor", max_length=120)),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("meta_cloud", "Meta WhatsApp Cloud API"),
                            ("twilio", "Twilio"),
                            ("other", "Otro"),
                        ],
                        max_length=30,
                    ),
                ),
                ("phone_number", models.CharField(help_text="Número de WhatsApp asignado (E.164)", max_length=30)),
                (
                    "business_id",
                    models.CharField(
                        blank=True,
                        help_text="Business ID (Meta) u otro identificador requerido",
                        max_length=64,
                    ),
                ),
                (
                    "phone_number_id",
                    models.CharField(
                        blank=True,
                        help_text="Phone Number ID (Meta) u otro identificador interno",
                        max_length=64,
                    ),
                ),
                ("api_token", models.CharField(help_text="Token/API key para enviar mensajes", max_length=512)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "is_managed",
                    models.BooleanField(
                        default=True,
                        help_text="Indica si la cuenta es administrada por AlojaSys",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Cuenta de Proveedor WhatsApp",
                "verbose_name_plural": "Cuentas de Proveedores WhatsApp",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="chatbotprovideraccount",
            index=models.Index(fields=["provider", "is_active"], name="chatbot_cha_provide_idx"),
        ),
        migrations.AddIndex(
            model_name="chatbotprovideraccount",
            index=models.Index(fields=["phone_number"], name="chatbot_cha_phone_idx"),
        ),
    ]


