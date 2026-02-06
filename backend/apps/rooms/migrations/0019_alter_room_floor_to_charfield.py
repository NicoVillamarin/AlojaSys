from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rooms", "0018_roomtype_alias"),
    ]

    operations = [
        migrations.AlterField(
            model_name="room",
            name="floor",
            field=models.CharField(max_length=20),
        ),
    ]

