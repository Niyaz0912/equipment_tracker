from django.contrib import admin
from django.utils.html import format_html
from .models import Location, NetworkEquipment, Subnet, IPAddress


class LocationAdmin(admin.ModelAdmin):
    """Админка для местоположений"""
    list_display = ('name', 'address', 'created_at')
    list_display_links = ('name',)
    search_fields = ('name', 'address', 'description')
    list_filter = ()
    fields = ('name', 'description', 'address')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('name')
    
    def created_at(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at.short_description = 'Дата создания'


class NetworkEquipmentAdmin(admin.ModelAdmin):
    """Админка для сетевого оборудования"""
    list_display = ('name', 'type_display', 'status_display', 'location_link', 'ip_address', 'created_short')
    list_display_links = ('name',)
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'model', 'serial_number', 'inventory_number', 'ip_address', 'mac_address')
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'type', 'model', 'status', 'notes')
        }),
        ('Идентификация', {
            'fields': ('serial_number', 'inventory_number'),
            'classes': ('collapse',)
        }),
        ('Размещение', {
            'fields': ('location', ('rack', 'unit'))
        }),
        ('Сетевая информация', {
            'fields': ('ip_address', 'mac_address')
        }),
        ('Системные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def type_display(self, obj):
        return obj.get_type_display()
    type_display.short_description = 'Тип'
    
    def status_display(self, obj):
        status_colors = {
            'active': 'green',
            'backup': 'blue',
            'repair': 'orange',
            'decommissioned': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    def location_link(self, obj):
        if obj.location:
            return format_html(
                '<a href="/admin/network/location/{}/change/">{}</a>',
                obj.location.id,
                obj.location.name
            )
        return "-"
    location_link.short_description = 'Местоположение'
    
    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    created_short.short_description = 'Создано'


class SubnetAdmin(admin.ModelAdmin):
    """Админка для подсетей"""
    list_display = ('network', 'description_short', 'purpose_display', 'location_link', 'date_added_short', 'ip_count')
    list_display_links = ('network',)
    list_filter = ('purpose', 'location')
    search_fields = ('network', 'description', 'comment', 'added_by')
    list_per_page = 30
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('network', 'description', 'purpose', 'location')
        }),
        ('Технические детали', {
            'fields': ('vlan_id', 'comment'),
            'classes': ('collapse',)
        }),
        ('Системные', {
            'fields': ('added_by', 'date_added'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_added',)
    
    def description_short(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Описание'
    
    def purpose_display(self, obj):
        purposes = {
            'client': '👥 Клиенты',
            'server': '🖥️ Серверы',
            'infrastructure': '🔧 Инфраструктура',
            'management': '⚙️ Управление',
            'dmz': '🛡️ DMZ',
            'wireless': '📶 Беспроводная',
            'other': '📁 Другое'
        }
        return purposes.get(obj.purpose, obj.get_purpose_display())
    purpose_display.short_description = 'Назначение'
    
    def location_link(self, obj):
        if obj.location:
            return format_html(
                '<a href="/admin/network/location/{}/change/">{}</a>',
                obj.location.id,
                obj.location.name
            )
        return "-"
    location_link.short_description = 'Локация'
    
    def date_added_short(self, obj):
        return obj.date_added.strftime('%d.%m.%Y')
    date_added_short.short_description = 'Добавлена'
    
    def ip_count(self, obj):
        count = IPAddress.objects.filter(subnet=obj).count()
        colors = {
            'free': 'blue',
            'occupied': 'green',
            'reserved': 'orange',
            'dynamic': 'purple'
        }
        
        status_counts = []
        for status_code, status_name in IPAddress.STATUS_CHOICES:
            status_count = IPAddress.objects.filter(subnet=obj, status=status_code).count()
            if status_count > 0:
                color = colors.get(status_code, 'gray')
                status_counts.append(
                    format_html(
                        '<span style="color: {}; margin-right: 5px;">{}: {}</span>',
                        color, status_name[:1], status_count
                    )
                )
        
        if status_counts:
            status_html = ''.join(status_counts)
            return format_html('{}<br>{}', count, status_html)
        return count
    ip_count.short_description = 'IP адреса'


class IPAddressAdmin(admin.ModelAdmin):
    """Админка для IP адресов"""
    list_display = ('address', 'subnet_link', 'status_display', 'device_link', 'description_short', 'last_updated_short')
    list_display_links = ('address',)
    list_filter = ('status', 'subnet', 'subnet__purpose')
    search_fields = ('address', 'mac_address', 'dns_name', 'description', 'note')
    list_per_page = 100
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('address', 'subnet', 'status', 'description')
        }),
        ('Привязка к оборудованию', {
            'fields': ('device', 'mac_address', 'dns_name')
        }),
        ('Дополнительно', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
        ('Системные', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('last_updated',)
    
    def subnet_link(self, obj):
        if obj.subnet:
            return format_html(
                '<a href="/admin/network/subnet/{}/change/">{}</a>',
                obj.subnet.id,
                obj.subnet.network
            )
        return "-"
    subnet_link.short_description = 'Подсеть'
    
    def status_display(self, obj):
        status_colors = {
            'free': 'blue',
            'occupied': 'green',
            'reserved': 'orange',
            'dynamic': 'purple'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    def device_link(self, obj):
        if obj.device:
            return format_html(
                '<a href="/admin/network/networkequipment/{}/change/">{}</a>',
                obj.device.id,
                obj.device.name
            )
        return "-"
    device_link.short_description = 'Оборудование'
    
    def description_short(self, obj):
        if obj.description and len(obj.description) > 40:
            return obj.description[:40] + '...'
        return obj.description or "-"
    description_short.short_description = 'Описание'
    
    def last_updated_short(self, obj):
        return obj.last_updated.strftime('%d.%m.%Y %H:%M')
    last_updated_short.short_description = 'Обновлено'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subnet', 'device')


# Регистрация моделей с кастомными админками
admin.site.register(Location, LocationAdmin)
admin.site.register(NetworkEquipment, NetworkEquipmentAdmin)
admin.site.register(Subnet, SubnetAdmin)
admin.site.register(IPAddress, IPAddressAdmin)