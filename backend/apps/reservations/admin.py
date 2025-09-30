from django.contrib import admin
from .models import Reservation, RoomBlock, ReservationChangeLog, ReservationStatusChange

@admin.register(Reservation)

class ReservationAdmin(admin.ModelAdmin):
    list_display = ["hotel", "room", "guest_name", "check_in", "check_out", "status", "total_price", "channel"]
    list_filter = ["hotel", "room", "status", "channel"]
    search_fields = ["guest_name", "room__name", "hotel__name", "guest_email"]
    list_editable = ["status"]
    list_select_related = ["hotel", "room"]


@admin.register(RoomBlock)
class RoomBlockAdmin(admin.ModelAdmin):
    list_display = ["hotel", "room", "block_type", "start_date", "end_date", "is_active"]
    list_filter = ["hotel", "block_type", "is_active"]
    search_fields = ["room__name", "reason"]
    list_select_related = ["hotel", "room"]

@admin.register(ReservationStatusChange)
class ReservationStatusChangeAdmin(admin.ModelAdmin):
    list_display = ["id", "reservation", "from_status", "to_status", "changed_at"]
    list_filter = ["from_status", "to_status"]
    search_fields = ["reservation__id"]

@admin.register(ReservationChangeLog)
class ReservationChangeLogAdmin(admin.ModelAdmin):
    list_display = ["id", "reservation", "event_type", "changed_at"]
    list_filter = ["event_type", "changed_at"]
    search_fields = ["reservation__id"]
