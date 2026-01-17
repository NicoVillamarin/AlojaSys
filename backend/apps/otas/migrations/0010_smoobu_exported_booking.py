from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("rooms", "0001_initial"),
        ("reservations", "0001_initial"),
        ("otas", "0009_alter_otaconfig_provider_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SmoobuExportedBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("reservation", "Reservation"), ("room_block", "RoomBlock")], max_length=20)),
                ("apartment_id", models.CharField(max_length=64)),
                ("smoobu_booking_id", models.CharField(max_length=64)),
                ("checksum", models.CharField(blank=True, max_length=64, null=True)),
                ("last_synced", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("hotel", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="smoobu_exported_bookings", to="core.hotel")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="smoobu_exported_bookings", to="rooms.room")),
                ("reservation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="smoobu_exported_bookings", to="reservations.reservation")),
                ("room_block", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="smoobu_exported_bookings", to="reservations.roomblock")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["hotel", "room", "kind"], name="otas_smoobu_hotel_room_kind_idx"),
                    models.Index(fields=["smoobu_booking_id"], name="otas_smoobu_booking_id_idx"),
                    models.Index(fields=["apartment_id"], name="otas_smoobu_apartment_id_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="smoobuexportedbooking",
            constraint=models.UniqueConstraint(condition=models.Q(("reservation__isnull", False)), fields=("reservation",), name="uniq_smoobu_exported_reservation"),
        ),
        migrations.AddConstraint(
            model_name="smoobuexportedbooking",
            constraint=models.UniqueConstraint(condition=models.Q(("room_block__isnull", False)), fields=("room_block",), name="uniq_smoobu_exported_room_block"),
        ),
    ]

