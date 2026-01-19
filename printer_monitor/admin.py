# printer_monitor/admin.py
from django.contrib import admin
from .models import (
    PrinterCheck,  # Добавьте старую модель
    PrinterStatusCheck, 
    PrinterDetailCheck, 
    PrinterCurrentStatus
)

# Регистрируем ВСЕ модели
admin.site.register(PrinterCheck)
admin.site.register(PrinterStatusCheck)
admin.site.register(PrinterDetailCheck)
admin.site.register(PrinterCurrentStatus)