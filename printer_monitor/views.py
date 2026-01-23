from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Q, OuterRef, Subquery
from django.utils import timezone
from datetime import timedelta

from equipments.models import Equipment
from .models import PrinterCheck, PrinterCurrentStatus
from .services import PrinterMonitorService
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required


class PrinterStatusView(LoginRequiredMixin, TemplateView):
    template_name = 'printer_monitor/status.html'  # переименуем в monitor.html
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Все принтеры
        printers = Equipment.objects.filter(type='printer').order_by('mc_number')
        
        # Сетевые принтеры (с IP)
        network_printers = printers.filter(ip_address__isnull=False)
        
        # Для каждого принтера получаем детальную информацию
        detailed_printers = []
        for printer in network_printers:
            current_status = PrinterCurrentStatus.objects.filter(printer=printer).first()
            last_check = PrinterCheck.objects.filter(printer=printer).order_by('-checked_at').first()
            
            # Uptime за 24 часа
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            checks_24h = PrinterCheck.objects.filter(
                printer=printer,
                checked_at__gte=twenty_four_hours_ago
            )
            
            uptime_24h = 0
            if checks_24h.exists():
                online_checks = checks_24h.filter(is_online=True).count()
                uptime_24h = round((online_checks / checks_24h.count()) * 100, 1)
            
            detailed_printers.append({
                'printer': printer,
                'current_status': current_status,
                'last_check': last_check,
                'uptime_24h': uptime_24h,
                'checks_24h': checks_24h.count(),
            })
        
        # Общая статистика
        total_stats = {
            'total': printers.count(),
            'with_ip': network_printers.count(),
            'without_ip': printers.filter(ip_address__isnull=True).count(),
            'online_now': PrinterCurrentStatus.objects.filter(
                printer__in=network_printers,
                is_online=True
            ).count(),
        }
        
        context.update({
            'detailed_printers': detailed_printers,
            'total_stats': total_stats,
            'last_update': timezone.now(),
        })
        
        return context



class PrinterStatsView(LoginRequiredMixin, TemplateView):
    template_name = 'printer_monitor/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        printers = Equipment.objects.filter(type='printer')
        
        # Основная статистика
        stats = printers.aggregate(
            total=Count('id'),
            with_ip=Count('id', filter=Q(ip_address__isnull=False)),
            without_ip=Count('id', filter=Q(ip_address__isnull=True)),
        )
        
        # Простая версия problem_printers (убери сервис пока)
        problem_printers = []
        for printer in printers.filter(ip_address__isnull=True):
            problem_printers.append({
                'printer': printer,
                'reason': 'Нет IP-адреса'
            })
        
        context.update({
            'stats': stats,
            'problem_printers': problem_printers[:10],  # Только 10 для теста
            'problem_count': len(problem_printers),
        })
        return context

class ProblemPrintersView(LoginRequiredMixin, ListView):
    """Список проблемных принтеров с пагинацией"""
    template_name = 'printer_monitor/problems.html'
    context_object_name = 'problems'
    paginate_by = 50
    
    def get_queryset(self):
        """Получаем проблемные принтеры через сервис"""
        return PrinterMonitorService.get_problem_printers()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_problems'] = len(self.get_queryset())
        return context


@login_required
@require_GET
def api_check_printer(request, ip):
    """API для проверки одного принтера"""
    result = PrinterMonitorService.check_printer(ip)
    return JsonResponse(result)

@login_required  
@require_GET
def api_check_all_printers(request):
    """API для проверки всех принтеров"""
    results = PrinterMonitorService.check_all_printers()
    online = sum(1 for r in results if r['result']['online'])
    return JsonResponse({
        'checked': len(results),
        'online': online,
        'offline': len(results) - online
    })