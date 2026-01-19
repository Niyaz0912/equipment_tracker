import socket
import time
from datetime import datetime
from django.db import transaction
from equipments.models import Equipment
from .models import PrinterCheck, PrinterStatusCheck, PrinterCurrentStatus

class PrinterMonitorService:
    """
    Сервис для мониторинга принтеров
    Вся бизнес-логика здесь
    """
    
    @staticmethod
    def check_printer_availability(printer):
        """Проверка доступности принтера"""
        if not printer.ip_address:
            return {'online': False, 'error': 'Нет IP-адреса'}
        
        ip = printer.ip_address
        result = {'printer': printer, 'ip': ip, 'online': False}
        
        try:
            # Порт 9100 - стандартный для JetDirect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            
            start_time = time.time()
            connection_result = sock.connect_ex((ip, 9100))
            response_time = (time.time() - start_time) * 1000  # мс
            
            if connection_result == 0:
                result['online'] = True
                result['response_time'] = round(response_time, 2)
                result['method'] = 'port_9100'
            else:
                # Пробуем порт 80 (HTTP)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                if sock.connect_ex((ip, 80)) == 0:
                    result['online'] = True
                    result['method'] = 'http'
                else:
                    result['error'] = 'Все порты закрыты'
                    
            sock.close()
            
        except socket.timeout:
            result['error'] = 'Таймаут соединения'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    @classmethod
    @transaction.atomic
    def save_check_result(cls, printer, result):
        """Сохраняем результат проверки"""
        # 1. Старая модель (для совместимости)
        PrinterCheck.objects.create(
            printer=printer,
            is_online=result['online'],
            response_time=result.get('response_time'),
            notes=result.get('error', '')
        )
        
        # 2. Новая модель быстрых проверок
        status_check = PrinterStatusCheck.objects.create(
            printer=printer,
            is_online=result['online'],
            response_time=result.get('response_time'),
            ping_success=result.get('method') == 'port_9100',
            http_success=result.get('method') == 'http',
            snmp_success=False
        )
        
        # 3. Обновляем текущий статус
        current, created = PrinterCurrentStatus.objects.get_or_create(
            printer=printer
        )
        
        if result['online']:
            current.is_online = True
            current.last_seen = datetime.now()
            current.response_time = result.get('response_time')
            current.status = 'online'
            current.has_errors = False
            current.last_error = ''
        else:
            current.is_online = False
            current.status = 'offline'
            current.has_errors = True
            current.last_error = result.get('error', 'Нет соединения')
        
        current.last_updated = datetime.now()
        current.save()
        
        return status_check
    
    @classmethod
    def check_all_printers(cls):
        """Проверить все принтеры с IP"""
        printers = Equipment.objects.filter(
            type='printer'
        ).exclude(
            ip_address__isnull=True
        ).exclude(
            ip_address=''
        )
        
        results = []
        for printer in printers:
            check_result = cls.check_printer_availability(printer)
            saved_check = cls.save_check_result(printer, check_result)
            results.append({
                'printer': printer.name,
                'online': check_result['online'],
                'response_time': check_result.get('response_time'),
                'check_id': saved_check.id
            })
        
        return results
    
    @classmethod
    def get_printer_statistics(cls):
        """Получить статистику по принтерам"""
        printers = Equipment.objects.filter(type='printer')
        printers_with_ip = printers.exclude(ip_address='').exclude(ip_address__isnull=True)
        
        # Текущие статусы
        current_statuses = PrinterCurrentStatus.objects.filter(
            printer__in=printers
        )
        
        online_count = current_statuses.filter(is_online=True).count()
        offline_count = current_statuses.filter(is_online=False).count()
        
        return {
            'total': printers.count(),
            'with_ip': printers_with_ip.count(),
            'online': online_count,
            'offline': offline_count,
            'availability': round((online_count / printers_with_ip.count() * 100), 1) if printers_with_ip.count() > 0 else 0
        }