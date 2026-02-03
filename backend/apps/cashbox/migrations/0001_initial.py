from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0019_remove_hotel_currency"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CashSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("open", "Abierta"), ("closed", "Cerrada"), ("cancelled", "Anulada")], default="open", max_length=12)),
                ("currency", models.CharField(default="ARS", max_length=3)),
                ("opened_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("opening_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("closing_amount", models.DecimalField(blank=True, decimal_places=2, help_text="Efectivo contado al cierre", max_digits=12, null=True)),
                ("expected_amount", models.DecimalField(blank=True, decimal_places=2, help_text="Efectivo esperado calculado al momento de cerrar (snapshot)", max_digits=12, null=True)),
                ("difference_amount", models.DecimalField(blank=True, decimal_places=2, help_text="Diferencia: closing_amount - expected_amount", max_digits=12, null=True)),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("closed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cash_sessions_closed", to=settings.AUTH_USER_MODEL)),
                ("hotel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cash_sessions", to="core.hotel")),
                ("opened_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cash_sessions_opened", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Sesión de caja",
                "verbose_name_plural": "Sesiones de caja",
                "ordering": ["-opened_at"],
                "permissions": [("open_cashsession", "Puede abrir caja"), ("close_cashsession", "Puede cerrar caja"), ("view_cashbox_reports", "Puede ver reportes de caja")],
            },
        ),
        migrations.CreateModel(
            name="CashMovement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("movement_type", models.CharField(choices=[("in", "Ingreso"), ("out", "Egreso")], max_length=8)),
                ("currency", models.CharField(default="ARS", max_length=3)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cash_movements_created", to=settings.AUTH_USER_MODEL)),
                ("hotel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cash_movements", to="core.hotel")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movements", to="cashbox.cashsession")),
            ],
            options={
                "verbose_name": "Movimiento de caja",
                "verbose_name_plural": "Movimientos de caja",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="cashsession",
            index=models.Index(fields=["hotel", "status"], name="cashbox_cas_hotel_i_9e4e0c_idx"),
        ),
        migrations.AddIndex(
            model_name="cashsession",
            index=models.Index(fields=["hotel", "opened_at"], name="cashbox_cas_hotel_i_60d8a7_idx"),
        ),
        migrations.AddIndex(
            model_name="cashsession",
            index=models.Index(fields=["hotel", "currency", "opened_at"], name="cashbox_cas_hotel_i_3ee05f_idx"),
        ),
        migrations.AddIndex(
            model_name="cashmovement",
            index=models.Index(fields=["hotel", "created_at"], name="cashbox_cas_hotel_i_62d2c6_idx"),
        ),
        migrations.AddIndex(
            model_name="cashmovement",
            index=models.Index(fields=["session", "created_at"], name="cashbox_cas_session_2a3c4e_idx"),
        ),
        migrations.AddIndex(
            model_name="cashmovement",
            index=models.Index(fields=["hotel", "currency", "created_at"], name="cashbox_cas_hotel_i_92f3a3_idx"),
        ),
    ]

