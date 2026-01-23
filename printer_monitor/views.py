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
    template_name = 'printer_monitor/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Получаем ВСЕ принтеры
        printers = Equipment.objects.filter(type='printer').order_by('mc_number')
        
        # 2. Считаем статистику ПРАВИЛЬНО
        stats = printers.aggregate(
            total=Count('id'),
            with_ip=Count('id', filter=Q(ip_address__isnull=False)),
            without_ip=Count('id', filter=Q(ip_address__isnull=True))
        )
        
        # 3. Получаем сетевые принтеры (с IP)
        network_printers = printers.filter(ip_address__isnull=False)
        
        # 4. Для каждого принтера получаем последний статус
        printer_statuses = []
        for printer in network_printers:
            try:
                current_status = PrinterCurrentStatus.objects.get(printer=printer)
                last_check = PrinterCheck.objects.filter(
                    printer=printer
                ).order_by('-checked_at').first()
                
                printer_statuses.append({
                    'printer': printer,
                    'current_status': current_status,
                    'last_check': last_check,
                })
            except PrinterCurrentStatus.DoesNotExist:
                # Если нет статуса, создаем пустой объект
                printer_statuses.append({
                    'printer': printer,
                    'current_status': None,
                    'last_check': None,
                })
        
        # 5. Получаем онлайн статусы
        online_count = PrinterCurrentStatus.objects.filter(
            printer__in=network_printers,
            is_online=True
        ).count()
        
        context.update({
            'printer_statuses': printer_statuses,  # Исправлено имя!
            'total_printers': stats['total'],      # Добавлено
            'printers_with_ip': stats['with_ip'],  # Добавлено
            'printers_without_ip': stats['without_ip'],  # Можно добавить
            'online_count': online_count,           # Добавлено
            'now': timezone.now(),
        })
        
        return context


class CheckPrintersView(LoginRequiredMixin, TemplateView):
    """Проверка всех принтеров"""
    template_name = 'printer_monitor/check.html'
    
    def post(self, request, *args, **kwargs):
        """POST запрос для проверки принтеров"""
        # Используем сервис для проверки
        results = PrinterMonitorService.check_all_printers()
    
        # Отладочная информация
        print(f"DEBUG: Получено {len(results)} результатов")
        if results:
            print(f"DEBUG: Первый результат keys: {results[0].keys()}")
    
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