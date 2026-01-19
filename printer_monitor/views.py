from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.contrib import messages
from equipments.models import Equipment
from .models import PrinterCurrentStatus, PrinterDetailCheck
from .services import PrinterMonitorService

class PrinterDashboardView(LoginRequiredMixin, TemplateView):
    """
    Дашборд со статусами всех принтеров
    """
    template_name = 'printer_monitor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем статистику
        stats = PrinterMonitorService.get_printer_statistics()
        
        # Получаем текущие статусы принтеров
        printers = Equipment.objects.filter(type='printer')
        current_statuses = PrinterCurrentStatus.objects.filter(
            printer__in=printers
        ).select_related('printer').order_by('printer__name')
        
        context.update({
            'stats': stats,
            'printers': current_statuses,
            'page_title': 'Мониторинг принтеров'
        })
        return context

class PrinterDetailView(LoginRequiredMixin, DetailView):
    """
    Детальная информация о принтере
    """
    model = Equipment
    template_name = 'printer_monitor/printer_detail.html'
    context_object_name = 'printer'
    
    def get_queryset(self):
        return Equipment.objects.filter(type='printer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        printer = self.object
        
        # Текущий статус
        current_status = PrinterCurrentStatus.objects.filter(
            printer=printer
        ).first()
        
        # История проверок (последние 20)
        from .models import PrinterStatusCheck
        recent_checks = PrinterStatusCheck.objects.filter(
            printer=printer
        ).order_by('-checked_at')[:20]
        
        # Детальные проверки
        detail_checks = PrinterDetailCheck.objects.filter(
            printer=printer
        ).order_by('-checked_at')[:10]
        
        context.update({
            'current_status': current_status,
            'recent_checks': recent_checks,
            'detail_checks': detail_checks,
            'last_24h_stats': self.get_last_24h_stats(printer)
        })
        return context
    
    def get_last_24h_stats(self, printer):
        """Статистика за последние 24 часа"""
        from django.utils import timezone
        from django.db.models import Count, Avg, Q
        from datetime import timedelta
        
        day_ago = timezone.now() - timedelta(hours=24)
        
        from .models import PrinterStatusCheck
        checks = PrinterStatusCheck.objects.filter(
            printer=printer,
            checked_at__gte=day_ago
        )
        
        if checks.exists():
            total = checks.count()
            online = checks.filter(is_online=True).count()
            
            return {
                'total_checks': total,
                'online_count': online,
                'uptime_percent': round((online / total * 100), 1) if total > 0 else 0,
                'avg_response': checks.filter(is_online=True).aggregate(
                    avg=Avg('response_time')
                )['avg']
            }
        return None

class CheckSinglePrinterView(LoginRequiredMixin, DetailView):
    """
    Проверка одного принтера (AJAX-совместимо)
    """
    model = Equipment
    http_method_names = ['post']  # Только POST
    
    def post(self, request, *args, **kwargs):
        printer = self.get_object()
        
        # Запускаем проверку
        result = PrinterMonitorService.check_printer_availability(printer)
        PrinterMonitorService.save_check_result(printer, result)
        
        # Для AJAX запросов
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'success': True,
                'online': result['online'],
                'printer': printer.name,
                'status': 'online' if result['online'] else 'offline'
            })
        
        # Для обычных запросов
        messages.success(
            request, 
            f"Принтер {printer.name}: {'✅ Онлайн' if result['online'] else '❌ Офлайн'}"
        )
        return redirect('printer_monitor:dashboard')

@require_POST
def check_all_printers_view(request):
    """
    Ручная проверка всех принтеров
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    results = PrinterMonitorService.check_all_printers()
    
    online_count = sum(1 for r in results if r['online'])
    total_count = len(results)
    
    messages.success(
        request,
        f"Проверено {total_count} принтеров. Онлайн: {online_count}"
    )
    
    return redirect('printer_monitor:dashboard')

class ProblemPrintersView(LoginRequiredMixin, ListView):
    """
    Список проблемных принтеров
    """
    template_name = 'printer_monitor/problem_printers.html'
    context_object_name = 'problem_printers'
    
    def get_queryset(self):
        # Принтеры, которые офлайн или с низким тонером
        return PrinterCurrentStatus.objects.filter(
            models.Q(is_online=False) | 
            models.Q(black_toner_level__lt=20) |
            models.Q(has_errors=True)
        ).select_related('printer').order_by('is_online', 'printer__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Группируем проблемы
        offline = self.get_queryset().filter(is_online=False)
        low_toner = self.get_queryset().filter(black_toner_level__lt=20)
        with_errors = self.get_queryset().filter(has_errors=True)
        
        context.update({
            'offline_count': offline.count(),
            'low_toner_count': low_toner.count(),
            'errors_count': with_errors.count(),
            'page_title': 'Проблемные принтеры'
        })
        return context