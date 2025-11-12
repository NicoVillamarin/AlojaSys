from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'phone', 'is_housekeeping_staff', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_housekeeping_staff', 'hotels')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'position')
    filter_horizontal = ('hotels',)
    readonly_fields = ('created_at', 'updated_at')
