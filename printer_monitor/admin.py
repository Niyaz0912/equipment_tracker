from django.contrib import admin
from .models import PrinterCheck

@admin.register(PrinterCheck)
class PrinterCheckAdmin(admin.ModelAdmin):
    list_display = ('printer', 'is_online', 'checked_at', 'response_time')
    list_filter = ('is_online', 'checked_at')
    search_fields = ('printer__mc_number', 'printer__brand', 'printer__model')
    readonly_fields = ('checked_at',)
    ordering = ('-checked_at',)
    
    def has_add_permission(self, request):
        # Запрещаем ручное добавление - только через мониторинг
        return False