# equipments/admin.py
from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('mc_number', 'type', 'brand', 'model', 'ip_address', 'status', 'assigned_to', 'assigned_department')
    list_filter = ('type', 'status', 'assigned_department')
    search_fields = ('mc_number', 'brand', 'model', 'ip_address')
    fieldsets = (
        ('Основная информация', {
            'fields': ('mc_number', 'type', 'brand', 'model', 'ip_address')
        }),
        ('Закрепление', {
            'fields': ('assigned_to', 'assigned_department')
        }),
        ('Статус и даты', {
            'fields': ('status', 'purchase_date', 'warranty_until', 'notes')
        }),
    )
    
    # Автозаполнение даты гарантии (например, +2 года от даты покупки)
    def save_model(self, request, obj, form, change):
        if obj.purchase_date and not obj.warranty_until:
            # По умолчанию гарантия 2 года
            from datetime import timedelta
            obj.warranty_until = obj.purchase_date + timedelta(days=365*2)
        super().save_model(request, obj, form, change)