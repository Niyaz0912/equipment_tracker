import socket
import time
from datetime import timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.db.models import Count, Q, OuterRef, Subquery, Case, When, Value, BooleanField, CharField
from django.db import transaction

from equipments.models import Equipment
from .models import PrinterCheck, PrinterCurrentStatus


class PrinterMonitorService:
    """Единый сервис для мониторинга принтеров"""
    
    # Статические константы
    COMMON_PORTS = [9100, 515, 631, 80, 443]
    DEFAULT_TIMEOUT = 2
    
    @staticmethod
    def _check_port(ip: str, port: int, timeout: float = 1.0) -> bool:
        """Внутренний метод проверки порта"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def check_printer(ip_address: str, port: int = 9100, timeout: int = 2) -> Dict:
        """
        Проверяет доступность принтера
        
        Returns:
            Dict с ключами: online, response_time, port, error
        """
        start_time = time.time()
        
        try:
            # Пробуем основной порт
            if PrinterMonitorService._check_port(ip_address, port, timeout):
                response_time = (time.time() - start_time) * 1000
                return {
                    'online': True,
                    'response_time': response_time,
                    'port': port,
                    'error': None
                }
            
            # Пробуем другие порты
            for test_port in PrinterMonitorService.COMMON_PORTS:
                if test_port != port and PrinterMonitorService._check_port(ip_address, test_port, 1):
                    response_time = (time.time() - start_time) * 1000
                    return {
                        'online': True,
                        'response_time': response_time,
                        'port': test_port,
                        'error': None
                    }
            
            return {
                'online': False,
                'response_time': (time.time() - start_time) * 1000,
                'port': None,
                'error': 'Все порты закрыты'
            }
            
        except socket.timeout:
            return {
                'online': False,
                'response_time': timeout * 1000,
                'port': None,
                'error': 'Таймаут соединения'
            }
        except Exception as e:
            return {
                'online': False,
                'response_time': 0,
                'port': None,
                'error': str(e)
            }
    
    @staticmethod
    def get_printer_summary() -> Dict:
        """Краткая сводка по принтерам - оптимизированная версия"""
        printers = Equipment.objects.filter(type='printer')
        
        # Все расчеты в одном запросе
        stats = printers.aggregate(
            total=Count('id'),
            with_ip=Count('id', filter=Q(ip_address__isnull=False)),
            without_ip=Count('id', filter=Q(ip_address__isnull=True))
        )
        
        # Получаем статусы за последний час
        hour_ago = timezone.now() - timedelta(hours=1)
        
        # Оптимизированный запрос для статусов
        recent_checks_subquery = PrinterCheck.objects.filter(
            printer=OuterRef('pk'),
            checked_at__gte=hour_ago
        ).order_by('-checked_at')
        
        printers_with_status = printers.filter(
            ip_address__isnull=False
        ).annotate(
            last_check_status=Subquery(recent_checks_subquery.values('is_online')[:1])
        )
        
        recently_online = sum(1 for p in printers_with_status if p.last_check_status is True)
        recently_offline = sum(1 for p in printers_with_status if p.last_check_status is False)
        
        return {
            **stats,
            'recently_online': recently_online,
            'recently_offline': recently_offline,
        }
    
    @staticmethod
    def update_printer_status(printer: Equipment, check_result: Dict) -> PrinterCurrentStatus:
        """Обновляет текущий статус принтера"""
        with transaction.atomic():
            current_status, created = PrinterCurrentStatus.objects.get_or_create(
                printer=printer,
                defaults={
                    'is_online': check_result['online'],
                    'last_updated': timezone.now(),
                    'status': 'online' if check_result['online'] else 'offline'
                }
            )
            
            if not created:
                current_status.is_online = check_result['online']
                current_status.last_updated = timezone.now()
                
                if check_result['online']:
                    current_status.last_seen = timezone.now()
                    current_status.response_time = check_result.get('response_time')
                    current_status.status = 'online'
                else:
                    current_status.status = 'offline'
                
                current_status.save()
            
            return current_status
    
    @staticmethod
    def check_all_printers() -> List[Dict]:
        """
        Проверяет все принтеры с IP-адресами
        Возвращает список результатов
        """
        printers = Equipment.objects.filter(
            type='printer',
            ip_address__isnull=False
        ).select_related('current_status')
        
        results = []
        checks_to_create = []
        
        for printer in printers:
            check_result = PrinterMonitorService.check_printer(printer.ip_address)
            
            # Подготавливаем объект проверки
            checks_to_create.append(PrinterCheck(
                printer=printer,
                is_online=check_result['online'],
                response_time=check_result.get('response_time'),
                notes=check_result.get('error', '')
            ))
            
            results.append({
                'printer': printer,
                'result': check_result
            })
        
        # Массовое создание проверок
        if checks_to_create:
            PrinterCheck.objects.bulk_create(checks_to_create)
            
            # Обновляем статусы
            for printer, check_result in zip(printers, results):
                PrinterMonitorService.update_printer_status(printer, check_result['result'])
        
        return results
    
    @staticmethod
    def get_problem_printers() -> List[Dict]:
        """
        Находит все проблемные принтеры с причинами
        Оптимизированный запрос без N+1
        """
        printers = Equipment.objects.filter(type='printer')
        
        # Аннотируем последнюю проверку
        last_check_subquery = PrinterCheck.objects.filter(
            printer=OuterRef('pk')
        ).order_by('-checked_at')
        
        printers = printers.annotate(
            last_check_time=Subquery(last_check_subquery.values('checked_at')[:1]),
            last_check_status=Subquery(last_check_subquery.values('is_online')[:1]),
            has_checks=Count('printer_checks')
        ).annotate(
            problem_reason=Case(
                # Нет IP
                When(ip_address__isnull=True, then=Value('Нет IP-адреса')),
                # Никогда не проверялся
                When(has_checks=0, then=Value('Никогда не проверялся')),
                # Офлайн
                When(last_check_status=False, then=Value('Офлайн')),
                # Давно не проверялся (>24 часа)
                When(
                    last_check_time__lt=timezone.now() - timedelta(hours=24),
                    then=Value('Давно не проверялся')
                ),
                default=Value('Нет проблем'),
                output_field=CharField()
            )
        ).filter(
            Q(problem_reason__in=[
                'Нет IP-адреса', 
                'Никогда не проверялся', 
                'Офлайн', 
                'Давно не проверялся'
            ])
        ).order_by('problem_reason', 'mc_number')
        
        # Формируем результат
        return [
            {
                'printer': printer,
                'reason': printer.problem_reason,
                'last_check': printer.last_check_time,
                'ip_address': printer.ip_address
            }
            for printer in printers
        ]