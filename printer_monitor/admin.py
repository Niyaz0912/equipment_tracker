from django.contrib import admin
from django.db.models import Count
from .models import PrinterCheck, PrinterCurrentStatus


@admin.register(PrinterCheck)
class PrinterCheckAdmin(admin.ModelAdmin):
    list_display = ['printer', 'checked_at', 'is_online', 'response_time']
    list_filter = ['is_online', 'checked_at']
    search_fields = ['printer__name', 'printer__mc_number']
    date_hierarchy = 'checked_at'
    ordering = ['-checked_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('printer')


@admin.register(PrinterCurrentStatus)
class PrinterCurrentStatusAdmin(admin.ModelAdmin):
    list_display = ['printer', 'status', 'is_online', 'last_updated', 'has_errors']
    list_filter = ['status', 'is_online', 'has_errors', 'has_warnings']
    search_fields = ['printer__name', 'printer__mc_number']
    readonly_fields = ['last_updated']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('printer')


# Если нужно, можно зарегистрировать другие модели, если они есть:
# from .models import PrinterDetailCheck, PrinterStatusCheck
# admin.site.register(PrinterDetailCheck)
# admin.site.register(PrinterStatusCheck)