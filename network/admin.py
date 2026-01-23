# network/admin.py
from django.contrib import admin
from .models import Location, NetworkEquipment

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(NetworkEquipment)
class NetworkEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'ip_address', 'status', 'location')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'ip_address')