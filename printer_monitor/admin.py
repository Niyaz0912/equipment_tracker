# printer_monitor/admin.py
from django.contrib import admin
from .models import PrinterCheck, PrinterCurrentStatus

@admin.register(PrinterCheck)
class PrinterCheckAdmin(admin.ModelAdmin):
    list_display = ['printer', 'checked_at', 'is_online', 'response_time']
    list_filter = ['is_online', 'checked_at']
    search_fields = ['printer__mc_number', 'printer__brand', 'printer__model']
    date_hierarchy = 'checked_at'

@admin.register(PrinterCurrentStatus)
class PrinterCurrentStatusAdmin(admin.ModelAdmin):
    list_display = ['printer', 'status', 'is_online', 'last_seen', 'last_updated']
    list_filter = ['status', 'is_online']
    search_fields = ['printer__mc_number', 'printer__brand', 'printer__model']