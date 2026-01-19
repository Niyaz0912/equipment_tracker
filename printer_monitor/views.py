from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from equipments.models import Equipment
from .models import PrinterCheck, PrinterCurrentStatus


class PrinterStatusView(LoginRequiredMixin, TemplateView):
    """Главная страница мониторинга принтеров"""
    template_name = 'printer_monitor/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Все принтеры
        printers = Equipment.objects.filter(type='printer').order_by('mc_number')
        
        # Для каждого принтера пробуем получить статус
        printer_data = []
        for printer in printers:
            # Пробуем получить текущий статус
            try:
                current_status = PrinterCurrentStatus.objects.get(printer=printer)
                last_check = PrinterCheck.objects.filter(
                    printer=printer
                ).order_by('-checked_at').first()
            except PrinterCurrentStatus.DoesNotExist:
                current_status = None
                last_check = None
            
            printer_data.append({
                'printer': printer,
                'current_status': current_status,
                'last_check': last_check,
                'has_ip': bool(printer.ip_address),
            })
        
        context.update({
            'total_printers': printers.count(),
            'printers_with_ip': printers.filter(ip_address__isnull=False).count(),
            'printer_data': printer_data,  # используем эту переменную!
            'now': timezone.now(),
        })
        return context

class CheckPrintersView(LoginRequiredMixin, TemplateView):
    """Ручная проверка всех принтеров"""
    template_name = 'printer_monitor/status.html'
    
    def get(self, request, *args, **kwargs):
        """Проверяем принтеры и показываем результаты"""
        from .services import check_printer
        
        printers_with_ip = Equipment.objects.filter(
            type='printer', 
            ip_address__isnull=False
        )
        
        checked_count = 0
        
        for printer in printers_with_ip:
            result = check_printer(printer.ip_address)
            PrinterCheck.objects.create(
                printer=printer,
                is_online=result['online'],
                response_time=result.get('response_time')
            )
            checked_count += 1
        
        messages.success(
            request, 
            f'Проверено {checked_count} принтеров'
        )
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Добавляем флаг, что только что проверили"""
        context = super().get_context_data(**kwargs)
        context['just_checked'] = True
        context['checked_count'] = Equipment.objects.filter(
            type='printer', ip_address__isnull=False
        ).count()
        return context


class PrinterStatsView(LoginRequiredMixin, TemplateView):
    """Статистика по принтерам"""
    template_name = 'printer_monitor/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        printers = Equipment.objects.filter(type='printer')
        
        # Основная статистика
        stats = {
            'total': printers.count(),
            'with_ip': printers.filter(ip_address__isnull=False).count(),
            # 'network': printers.filter(connection_type='network').count(),
            # 'usb': printers.filter(connection_type='usb').count(),
            'network': printers.filter(ip_address__isnull=False).count(),
            'usb': printers.filter(ip_address__isnull=True).count(),
        }
        
        # По отделам
        by_department = printers.values(
            'assigned_department__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # По статусу (последние 24 часа)
        day_ago = timezone.now() - timedelta(hours=24)
        recent_checks = PrinterCheck.objects.filter(
            checked_at__gte=day_ago
        )
        
        if recent_checks.exists():
            online_count = recent_checks.filter(is_online=True).count()
            uptime = (online_count / recent_checks.count()) * 100
        else:
            uptime = 0
        
        context.update({
            'stats': stats,
            'by_department': by_department,
            'uptime_24h': round(uptime, 1),
            'problem_printers': self.get_problem_printers(),
        })
        return context
    
    def get_problem_printers(self):
        """Находим принтеры с проблемами"""
        printers = Equipment.objects.filter(type='printer')
    
        problems = []
        for printer in printers:
            # Проверяем, есть ли IP
            if not printer.ip_address:
                problems.append((printer, 'Нет IP-адреса'))
            else:
                # Проверяем последнюю проверку
                from .models import PrinterCheck
                last_check = PrinterCheck.objects.filter(
                    printer=printer
                ).order_by('-checked_at').first()
            
                if not last_check:
                    problems.append((printer, 'Никогда не проверялся'))
                elif not last_check.is_online:
                    problems.append((printer, 'Офлайн'))
    
        return problems

class ProblemPrintersView(LoginRequiredMixin, ListView):
    """Список проблемных принтеров"""
    template_name = 'printer_monitor/problems.html'
    context_object_name = 'problems'
    
    def get_queryset(self):
        """Находим принтеры с проблемами"""
        problems = []
        printers = Equipment.objects.filter(type='printer')
        
        for printer in printers:
            status = self.get_printer_status(printer)
            if status['has_problems']:
                problems.append({
                    'printer': printer,
                    'status': status
                })
        
        return problems
    
    def get_printer_status(self, printer):
        """Определяем статус принтера"""
        last_check = PrinterCheck.objects.filter(
            printer=printer
        ).order_by('-checked_at').first()
        
        if not last_check:
            return {'has_problems': True, 'reason': 'Не проверялся'}
        
        time_since_check = timezone.now() - last_check.checked_at
        
        if not last_check.is_online:
            return {'has_problems': True, 'reason': 'Офлайн'}
        elif time_since_check > timedelta(hours=24):
            return {'has_problems': True, 'reason': 'Давно не проверялся'}
        
        return {'has_problems': False}