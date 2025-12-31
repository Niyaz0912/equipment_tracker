# equipments/admin.py
from django.contrib import admin
from .models import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('mc_number', 'type', 'brand', 'model', 'assigned_to', 'status', 'purchase_date')
    list_filter = ('type', 'status', 'assigned_to__department')
    search_fields = ('mc_number', 'brand', 'model', 'serial_number', 'assigned_to__last_name', 'assigned_to__first_name')
    ordering = ('mc_number',)
    list_select_related = ('assigned_to',)
    
    # Группировка полей в форме
    fieldsets = (
        ('Основная информация', {
            'fields': ('mc_number', 'type', 'brand', 'model', 'serial_number')
        }),
        ('Принадлежность', {
            'fields': ('assigned_to', 'status')
        }),
        ('Дополнительно', {
            'fields': ('purchase_date', 'warranty_until', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    # Автозаполнение даты гарантии (например, +2 года от даты покупки)
    def save_model(self, request, obj, form, change):
        if obj.purchase_date and not obj.warranty_until:
            # По умолчанию гарантия 2 года
            from datetime import timedelta
            obj.warranty_until = obj.purchase_date + timedelta(days=365*2)
        super().save_model(request, obj, form, change)