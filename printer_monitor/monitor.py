"""
Самый простой монитор - только проверка доступности
"""
import socket
from datetime import datetime

def check_printer_simple(ip_address, port=9100, timeout=3):
    """
    Проверяет, доступен ли принтер по IP и порту
    Возвращает: (is_online, response_time, error_message)
    """
    start_time = datetime.now()
    
    try:
        # Создаем сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Пытаемся подключиться
        result = sock.connect_ex((ip_address, port))
        
        # Закрываем сокет
        sock.close()
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000  # мс
        
        if result == 0:
            return True, round(response_time, 2), "Принтер доступен"
        else:
            return False, None, f"Порт {port} закрыт"
            
    except socket.timeout:
        return False, None, f"Таймаут ({timeout} сек)"
    except socket.error as e:
        return False, None, f"Ошибка подключения: {str(e)}"
    except Exception as e:
        return False, None, f"Неизвестная ошибка: {str(e)}"

def check_all_printers_from_db():
    """
    Проверяет все принтеры, у которых есть IP-адрес
    """
    from equipments.models import Equipment
    from .models import PrinterCheck
    
    printers = Equipment.objects.filter(
        type='Принтер',
        ip_address__isnull=False
    ).exclude(ip_address='')
    
    results = []
    
    for printer in printers:
        ip = printer.ip_address
        
        if ip:
            is_online, response_time, error_msg = check_printer_simple(ip)
            
            # Сохраняем результат в БД
            check = PrinterCheck.objects.create(
                printer=printer,
                is_online=is_online,
                response_time=response_time,
                notes=error_msg
            )
            
            results.append({
                'printer': printer,
                'is_online': is_online,
                'response_time': response_time,
                'error': error_msg,
                'check': check
            })
    
    return results