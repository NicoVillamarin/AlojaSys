from django.db import migrations, models
import django.db.models.deletion


def forwards_backfill_hotel_currency(apps, schema_editor):
    Hotel = apps.get_model("core", "Hotel")
    Currency = apps.get_model("core", "Currency")

    # Asegurar ARS como fallback
    ars, _ = Currency.objects.get_or_create(code="ARS", defaults={"name": "ARS"})

    # Backfill: mapear el viejo Hotel.currency (CharField) -> currency_fk (FK)
    for hotel in Hotel.objects.all().only("id", "currency"):
        raw = getattr(hotel, "currency", None)
        code = (str(raw).strip().upper() if raw else "") or "ARS"
        curr, _ = Currency.objects.get_or_create(code=code, defaults={"name": code})
        setattr(hotel, "currency_fk", curr)
        hotel.save(update_fields=["currency_fk"])


def backwards_noop(apps, schema_editor):
    # No-op: esta migración es parte de un swap posterior.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_currency_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="hotel",
            name="currency_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="hotels_tmp",
                to="core.currency",
            ),
        ),
        migrations.RunPython(forwards_backfill_hotel_currency, backwards_noop),
    ]

