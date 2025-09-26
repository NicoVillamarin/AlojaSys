from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0002_city_postal_code"),
        ("enterprises", "0004_create_enterprises_table_if_missing"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="enterprise",
                    name="country",
                    field=models.ForeignKey(
                        to="locations.country",
                        on_delete=models.PROTECT,
                        related_name="enterprises",
                        null=True,
                        blank=True,
                    ),
                ),
                migrations.AddField(
                    model_name="enterprise",
                    name="state",
                    field=models.ForeignKey(
                        to="locations.state",
                        on_delete=models.PROTECT,
                        related_name="enterprises",
                        null=True,
                        blank=True,
                    ),
                ),
                migrations.AddField(
                    model_name="enterprise",
                    name="city",
                    field=models.ForeignKey(
                        to="locations.city",
                        on_delete=models.PROTECT,
                        related_name="enterprises",
                        null=True,
                        blank=True,
                    ),
                ),
            ],
        ),
    ]


