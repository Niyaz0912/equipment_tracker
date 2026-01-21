# printer_monitor/services.py - ТОЛЬКО СЕРВИС
import socket
import time
from datetime import timedelta
from typing import Dict, List
from django.utils import timezone
from django.db.models import Count, Q
from django.db import transaction

from equipments.models import Equipment
from .models import PrinterCheck, PrinterCurrentStatus


class PrinterMonitorService:
    COMMON_PORTS = [9100, 515, 631, 80, 443]
    
    @staticmethod
    def _check_port(ip: str, port: int, timeout: float = 1.0) -> bool:
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
        start_time = time.time()
        
        try:
            if PrinterMonitorService._check_port(ip_address, port, timeout):
                response_time = (time.time() - start_time) * 1000
                return {
                    'online': True,
                    'response_time': response_time,
                    'port': port,
                    'error': None
                }
            
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
    def update_printer_status(printer: Equipment, check_result: Dict) -> PrinterCurrentStatus:
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
        printers = Equipment.objects.filter(
            type='printer',
            ip_address__isnull=False
        )
        
        results = []
        
        for printer in printers:
            check_result = PrinterMonitorService.check_printer(printer.ip_address)
            
            PrinterCheck.objects.create(
                printer=printer,
                is_online=check_result['online'],
                response_time=check_result.get('response_time'),
                notes=check_result.get('error', '')
            )
            
            PrinterMonitorService.update_printer_status(printer, check_result)
            
            results.append({
                'printer': printer,
                'result': check_result
            })
        
        return results