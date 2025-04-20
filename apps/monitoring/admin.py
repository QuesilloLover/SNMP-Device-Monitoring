from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin interface for the Device model.
    """
    list_display = ('name', 'ip_address', 'port', 'community')
    search_fields = ('name', 'ip_address')
    list_filter = ('port',)

