from django.contrib import admin
from .models import Country, State, City

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code2", "code3", "phone_code", "currency_code", "created_at")
    search_fields = ("name", "code2", "code3", "currency_code")
    list_per_page = 25

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "code", "created_at")
    list_filter = ("country",)
    search_fields = ("name", "code", "country__name", "country__code2")
    list_select_related = ("country",)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    @admin.display(ordering="state__country__name", description="Country")
    def country(self, obj):
        return obj.state.country
    list_display = ("name", "state", "country", "created_at")
    list_filter = ("state", "state__country")
    search_fields = ("name", "state__name", "state__country__name", "state__country__code2")
    list_select_related = ("state", "state__country")