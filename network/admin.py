from django.contrib import admin
from .models import Location, NetworkEquipment, NetworkDevice, Subnet

@admin.register(NetworkEquipment)
class NetworkEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'location', 'ip_address', 'created_at')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'model', 'serial_number', 'inventory_number', 'ip_address')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'type', 'model', 'status')
        }),
        ('Идентификационные номера', {
            'fields': ('serial_number', 'inventory_number'),
            'classes': ('collapse',)
        }),
        ('Размещение', {
            'fields': ('location', 'rack', 'unit')
        }),
        ('Сетевая информация', {
            'fields': ('ip_address', 'mac_address')
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')  # УБРАЛ 'created_at'
    search_fields = ('name', 'address', 'description')
    # УБРАЛ list_filter так как нет полей для фильтрации


# Пока оставляем пустые админки для зарезервированных моделей
@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    pass


@admin.register(Subnet)
class SubnetAdmin(admin.ModelAdmin):
    pass