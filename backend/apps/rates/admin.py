from django.contrib import admin
from .models import RatePlan, RateRule, RateOccupancyPrice, PromoRule, TaxRule

class RateOccupancyPriceInline(admin.TabularInline):
    model = RateOccupancyPrice
    extra = 1

@admin.register(RateRule)
class RateRuleAdmin(admin.ModelAdmin):
    list_display = ("plan", "name", "start_date", "end_date", "priority", "channel", "closed")
    list_filter = ("plan", "channel", "closed", "target_room_type", "target_room")
    search_fields = ("name", "plan__name")
    inlines = [RateOccupancyPriceInline]

@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "priority", "hotel")
    list_filter = ("is_active", "hotel")
    search_fields = ("name", "code", "hotel__name")


@admin.register(PromoRule)
class PromoRuleAdmin(admin.ModelAdmin):
    list_display = ("hotel", "name", "code", "priority", "is_active", "start_date", "end_date")
    list_filter = ("hotel", "is_active", "channel", "target_room_type")
    search_fields = ("name", "code")


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ("hotel", "name", "percent", "priority", "is_active", "channel")
    list_filter = ("hotel", "is_active")
    search_fields = ("name",)
