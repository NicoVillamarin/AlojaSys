from django.db import migrations, models
import django.db.models.deletion


def forwards_ensure_not_null(apps, schema_editor):
    Hotel = apps.get_model("core", "Hotel")
    Currency = apps.get_model("core", "Currency")
    ars, _ = Currency.objects.get_or_create(code="ARS", defaults={"name": "ARS"})

    for hotel in Hotel.objects.all().only("id", "currency_fk"):
        if getattr(hotel, "currency_fk_id", None) is None:
            hotel.currency_fk = ars
            hotel.save(update_fields=["currency_fk"])


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0017_hotel_currency_fk"),
    ]

    operations = [
        migrations.RunPython(forwards_ensure_not_null, backwards_noop),
        migrations.RemoveField(
            model_name="hotel",
            name="currency",
        ),
        migrations.RenameField(
            model_name="hotel",
            old_name="currency_fk",
            new_name="currency",
        ),
        migrations.AlterField(
            model_name="hotel",
            name="currency",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="hotels",
                to="core.currency",
            ),
        ),
    ]

