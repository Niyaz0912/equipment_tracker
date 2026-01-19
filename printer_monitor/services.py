import socket
import time
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from .models import PrinterCheck, PrinterCurrentStatus
from equipments.models import Equipment


def check_printer(ip_address, port=9100, timeout=2):
    """
    Проверяет доступность принтера по TCP порту
    
    Args:
        ip_address: IP принтера
        port: порт для проверки (обычно 9100 для печати)
        timeout: таймаут в секундах
    
    Returns:
        dict: {'online': bool, 'response_time': float, 'error': str}
    """
    start_time = time.time()
    
    try:
        # Пробуем подключиться к порту принтера
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        response_time = (time.time() - start_time) * 1000  # в мс
        
        if result == 0:
            return {
                'online': True,
                'response_time': response_time,
                'port': port
            }
        
        # Если основной порт не ответил, пробуем другие порты
        common_printer_ports = [9100, 515, 631, 80, 443]
        
        for port in common_printer_ports:
            if check_port(ip_address, port, timeout):
                return {
                    'online': True,
                    'response_time': response_time,
                    'port': port
                }
        
        return {
            'online': False,
            'response_time': response_time,
            'error': 'Все порты закрыты'
        }
        
    except socket.timeout:
        return {
            'online': False,
            'response_time': timeout * 1000,
            'error': 'Таймаут'
        }
    except Exception as e:
        return {
            'online': False,
            'response_time': 0,
            'error': str(e)
        }


def check_port(ip, port, timeout=1):
    """Быстрая проверка конкретного порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False


def get_printer_summary():
    """Краткая сводка по принтерам для дашборда"""
    printers = Equipment.objects.filter(type='printer')
    
    summary = {
        'total': printers.count(),
        'with_ip': printers.filter(ip_address__isnull=False).count(),
        'recently_online': 0,
        'recently_offline': 0,
    }
    
    # Проверяем статус за последний час
    hour_ago = timezone.now() - timedelta(hours=1)
    
    for printer in printers.filter(ip_address__isnull=False):
        last_check = PrinterCheck.objects.filter(
            printer=printer,
            checked_at__gte=hour_ago
        ).order_by('-checked_at').first()
        
        if last_check:
            if last_check.is_online:
                summary['recently_online'] += 1
            else:
                summary['recently_offline'] += 1
    
    return summary


def update_printer_status(printer, check_result):
    """
    Обновляет текущий статус принтера после проверки
    
    Args:
        printer: объект Equipment (принтер)
        check_result: результат от check_printer()
    """
    # Получаем или создаем текущий статус
    current_status, created = PrinterCurrentStatus.objects.get_or_create(
        printer=printer
    )
    
    # Обновляем поля
    current_status.is_online = check_result['online']
    current_status.last_updated = timezone.now()
    
    if check_result['online']:
        current_status.last_seen = timezone.now()
        current_status.response_time = check_result.get('response_time')
        current_status.status = 'online'
    else:
        current_status.status = 'offline'
    
    # Сохраняем
    current_status.save()
    
    return current_status


def check_all_printers():
    """
    Проверяет все принтеры с IP-адресами
    
    Returns:
        list: результаты проверки каждого принтера
    """
    printers = Equipment.objects.filter(
        type='printer',
        ip_address__isnull=False
    )
    
    results = []
    
    for printer in printers:
        # Проверяем принтер
        check_result = check_printer(printer.ip_address)
        
        # Сохраняем проверку
        printer_check = PrinterCheck.objects.create(
            printer=printer,
            is_online=check_result['online'],
            response_time=check_result.get('response_time'),
            notes=check_result.get('error', '')
        )
        
        # Обновляем текущий статус
        update_printer_status(printer, check_result)
        
        results.append({
            'printer': printer,
            'check': printer_check,
            'result': check_result
        })
    
    return results


def get_problem_printers():
    """
    Находит принтеры с проблемами
    
    Returns:
        list: принтеры с проблемами и причинами
    """
    problems = []
    
    # Принтеры с IP, которые офлайн
    printers_with_ip = Equipment.objects.filter(
        type='printer',
        ip_address__isnull=False
    )
    
    for printer in printers_with_ip:
        last_check = PrinterCheck.objects.filter(
            printer=printer
        ).order_by('-checked_at').first()
        
        if not last_check:
            problems.append((printer, 'Никогда не проверялся'))
        elif not last_check.is_online:
            problems.append((printer, 'Офлайн'))
        elif last_check.checked_at < timezone.now() - timedelta(hours=24):
            problems.append((printer, 'Давно не проверялся'))
    
    return problems