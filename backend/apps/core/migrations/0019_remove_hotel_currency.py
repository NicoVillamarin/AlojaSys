from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0013_room_base_currency_not_null"),
        ("core", "0018_hotel_currency_swap"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="hotel",
            name="currency",
        ),
    ]

