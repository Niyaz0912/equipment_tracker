# history/admin.py
from django.contrib import admin
from .models import EquipmentHistory

@admin.register(EquipmentHistory)
class EquipmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'employee', 'action', 'date', 'created_by')
    list_filter = ('action', 'date', 'employee__department')
    search_fields = ('equipment__mc_number', 'employee__last_name', 'employee__first_name', 'notes')
    ordering = ('-date', '-id')
    
    # Автозаполнение поля created_by
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)