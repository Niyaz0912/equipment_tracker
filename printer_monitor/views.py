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


class PrinterStatusView(LoginRequiredMixin, TemplateView):
    """Главная страница мониторинга принтеров"""
    template_name = 'printer_monitor/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Оптимизированный запрос всех принтеров с их статусами
        printers = Equipment.objects.filter(type='printer').order_by('mc_number')
        
        # Аннотируем последнюю проверку и текущий статус
        last_check_subquery = PrinterCheck.objects.filter(
            printer=OuterRef('pk')
        ).order_by('-checked_at')
        
        printers = printers.annotate(
            last_check_time=Subquery(last_check_subquery.values('checked_at')[:1]),
            last_check_online=Subquery(last_check_subquery.values('is_online')[:1]),
            last_check_response=Subquery(last_check_subquery.values('response_time')[:1]),
        )
        
        # Получаем текущие статусы
        status_dict = {
            status.printer_id: status 
            for status in PrinterCurrentStatus.objects.filter(
                printer__in=printers
            ).select_related('printer')
        }
        
        # Формируем данные для шаблона
        printer_data = []
        for printer in printers:
            current_status = status_dict.get(printer.id)
            
            printer_data.append({
                'printer': printer,
                'current_status': current_status,
                'last_check': {
                    'time': printer.last_check_time,
                    'is_online': printer.last_check_online,
                    'response_time': printer.last_check_response,
                } if printer.last_check_time else None,
                'has_ip': bool(printer.ip_address),
            })
        
        # Получаем сводку через сервис
        summary = PrinterMonitorService.get_printer_summary()
        
        context.update({
            'printer_data': printer_data,
            'summary': summary,
            'now': timezone.now(),
            'problem_count': len(PrinterMonitorService.get_problem_printers()),
        })
        return context


class CheckPrintersView(LoginRequiredMixin, TemplateView):
    """Проверка всех принтеров"""
    template_name = 'printer_monitor/check.html'
    
    def post(self, request, *args, **kwargs):
        """POST запрос для проверки принтеров"""
        # Используем сервис для проверки
        results = PrinterMonitorService.check_all_printers()
        
        messages.success(
            request, 
            f'Проверено {len(results)} принтеров'
        )
        
        context = self.get_context_data(**kwargs)
        context['check_results'] = results
        return self.render_to_response(context)
    
    def get(self, request, *args, **kwargs):
        """GET запрос показывает страницу с кнопкой проверки"""
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['printers_count'] = Equipment.objects.filter(
            type='printer', 
            ip_address__isnull=False
        ).count()
        return context


class PrinterStatsView(LoginRequiredMixin, TemplateView):
    """Статистика по принтерам"""
    template_name = 'printer_monitor/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        printers = Equipment.objects.filter(type='printer')
        
        # Основная статистика через агрегацию
        stats = printers.aggregate(
            total=Count('id'),
            with_ip=Count('id', filter=Q(ip_address__isnull=False)),
            without_ip=Count('id', filter=Q(ip_address__isnull=True)),
        )
        
        # Статистика по отделам
        by_department = printers.values(
            'assigned_department__name'
        ).annotate(
            count=Count('id'),
            with_ip=Count('id', filter=Q(ip_address__isnull=False))
        ).order_by('-count')
        
        # Uptime за 24 часа
        day_ago = timezone.now() - timedelta(hours=24)
        recent_stats = PrinterCheck.objects.filter(
            checked_at__gte=day_ago
        ).aggregate(
            total=Count('id'),
            online=Count('id', filter=Q(is_online=True))
        )
        
        uptime = (
            (recent_stats['online'] / recent_stats['total'] * 100) 
            if recent_stats['total'] > 0 else 0
        )
        
        # Проблемные принтеры через сервис
        problem_printers = PrinterMonitorService.get_problem_printers()
        
        context.update({
            'stats': stats,
            'by_department': by_department,
            'uptime_24h': round(uptime, 1),
            'problem_printers': problem_printers[:10],  # Только 10 для статистики
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