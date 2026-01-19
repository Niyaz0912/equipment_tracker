from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from equipments.models import Equipment
from .models import PrinterCheck
from .monitor import check_all_printers_from_db

class PrinterStatusView(LoginRequiredMixin, TemplateView):
    """
    Простейшая страница со статусом принтеров
    """
    template_name = 'printer_monitor/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Все принтеры
        printers = Equipment.objects.filter(type='printer')
        
        # Последняя проверка для каждого принтера
        printer_statuses = []
        for printer in printers:
            last_check = PrinterCheck.objects.filter(
                printer=printer
            ).order_by('-checked_at').first()
            
            printer_statuses.append({
                'printer': printer,
                'last_check': last_check,
                'has_ip': bool(printer.ip_address)
            })
        
        context['printer_statuses'] = printer_statuses
        context['total_printers'] = printers.count()
        context['printers_with_ip'] = printers.exclude(ip_address='').count()
        
        return context

def check_printers_now(request):
    """
    Ручная проверка всех принтеров
    """
    if not request.user.is_authenticated:
        return render(request, 'printer_monitor/status.html', {})
    
    # Запускаем проверку
    results = check_all_printers_from_db()
    
    # Обновляем контекст
    printers = Equipment.objects.filter(type='Принтер')
    printer_statuses = []
    
    for printer in printers:
        last_check = PrinterCheck.objects.filter(
            printer=printer
        ).order_by('-checked_at').first()
        
        printer_statuses.append({
            'printer': printer,
            'last_check': last_check,
            'has_ip': bool(printer.ip_address)
        })
    
    return render(request, 'printer_monitor/status.html', {
        'printer_statuses': printer_statuses,
        'total_printers': printers.count(),
        'printers_with_ip': printers.exclude(ip_address='').count(),
        'just_checked': True,
        'checked_count': len(results)
    })