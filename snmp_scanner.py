# snmp_scanner.py
from easysnmp import Session, EasySNMPError
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_device_info(ip, community='public'):
    """Получает информацию об устройстве через SNMP"""
    device = {
        'ip': ip,
        'hostname': None,
        'model': None,
        'serial': None,
        'description': None,
        'location': None,
        'uptime': None,
        'device_type': 'unknown',
        'success': False,
        'error': None
    }
    
    try:
        # Создаем сессию SNMP (version=2 означает SNMP v2c)
        session = Session(
            hostname=ip,
            community=community,
            version=2,
            timeout=2,
            retries=1
        )
        
        # Запрашиваем базовую информацию
        # sysDescr - описание устройства (часто содержит модель)
        # sysName - имя устройства
        # sysLocation - местоположение
        # sysUpTime - время работы
        results = session.get_bulk(['sysDescr', 'sysName', 'sysLocation', 'sysUpTime'])
        
        # Разбираем результаты
        for item in results:
            oid = item.oid
            value = item.value
            
            if oid == 'sysDescr.0':
                device['description'] = value
                # Пытаемся определить тип по описанию
                desc_lower = value.lower()
                if 'cisco' in desc_lower:
                    device['device_type'] = 'Cisco Switch/Router'
                elif 'hp' in desc_lower or 'hpe' in desc_lower or 'aruba' in desc_lower:
                    device['device_type'] = 'HP/Aruba Switch'
                elif 'd-link' in desc_lower:
                    device['device_type'] = 'D-Link Switch'
                elif 'mikrotik' in desc_lower:
                    device['device_type'] = 'MikroTik Router'
                elif 'router' in desc_lower:
                    device['device_type'] = 'Router'
                elif 'switch' in desc_lower:
                    device['device_type'] = 'Switch'
                elif 'firewall' in desc_lower:
                    device['device_type'] = 'Firewall'
                
            elif oid == 'sysName.0':
                device['hostname'] = value
            elif oid == 'sysLocation.0':
                device['location'] = value
            elif oid == 'sysUpTime.0':
                device['uptime'] = value
        
        device['success'] = True
        
        # Пробуем получить серийный номер (OID может отличаться для разных вендоров)
        try:
            # Общие OID для серийных номеров
            serial_oids = [
                '1.3.6.1.2.1.47.1.1.1.1.11.1',  # Для Cisco и других
                '1.3.6.1.4.1.9.3.6.3.0',        # Cisco серийный
                '1.3.6.1.4.1.11.2.3.1.1.8.0',   # HP серийный
            ]
            
            for oid in serial_oids:
                try:
                    serial = session.get(oid)
                    if serial.value and serial.value != '':
                        device['serial'] = serial.value
                        break
                except:
                    continue
        except:
            pass  # Если не получили серийник - не страшно
        
        # Извлекаем модель из описания
        if device['description']:
            desc = device['description']
            # Ищем модели типа WS-C2960, Catalyst, SG300 и т.д.
            import re
            model_patterns = [
                r'(WS-[A-Z]\d+[A-Z]?\d*)',  # Cisco WS-C2960X
                r'(Catalyst\s+\S+)',         # Catalyst 2960
                r'(SG\d+)',                   # SG300
                r'(SRW\d+)',                  # D-Link SRW
                r'(DES-\d+)',                 # D-Link DES-3200
            ]
            
            for pattern in model_patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    device['model'] = match.group(1)
                    break
            
            # Если не нашли по шаблону, берем первые слова
            if not device['model']:
                words = desc.split()
                if len(words) > 1:
                    device['model'] = ' '.join(words[:2])[:50]
        
    except EasySNMPError as e:
        device['error'] = str(e)
    except Exception as e:
        device['error'] = f"Ошибка подключения: {e}"
    
    return device

def main():
    print("🔍 SNMP Scanner для сетевого оборудования")
    print("=" * 50)
    
    # Читаем найденные IP из предыдущего сканирования
    try:
        with open('active_hosts.txt', 'r') as f:
            all_ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Файл active_hosts.txt не найден. Сначала запустите network_scanner.py")
        return
    
    print(f"📋 Всего IP для проверки: {len(all_ips)}")
    
    # Для теста берем первые 30 IP
    test_ips = all_ips[:30]
    print(f"🔬 Проверяем первые {len(test_ips)} устройств...")
    
    devices = []
    successful = 0
    
    # Проверяем устройства через SNMP
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(get_device_info, ip, 'public'): ip for ip in test_ips}
        
        for future in as_completed(future_to_ip):
            device = future.result()
            devices.append(device)
            
            ip = future_to_ip[future]
            if device['success']:
                successful += 1
                symbol = '✅' if device['device_type'] != 'unknown' else 'ℹ️'
                print(f"{symbol} {ip}: {device['hostname'] or 'Без имени'} - {device['device_type']}")
            else:
                print(f"❌ {ip}: Не отвечает на SNMP")
    
    # Фильтруем только успешные результаты
    network_devices = [d for d in devices if d['success'] and d['device_type'] != 'unknown']
    
    print(f"\n📊 Результаты за {time.time() - start_time:.1f} секунд:")
    print(f"   Всего проверено: {len(devices)}")
    print(f"   Ответили на SNMP: {successful}")
    print(f"   Сетевое оборудование: {len(network_devices)}")
    
    # Сохраняем результаты
    if network_devices:
        with open('network_equipment.json', 'w', encoding='utf-8') as f:
            json.dump(network_devices, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Данные сохранены в 'network_equipment.json'")
        
        # Группируем по типам
        from collections import Counter
        types = Counter([d['device_type'] for d in network_devices])
        
        print("\n📈 Типы сетевого оборудования:")
        for device_type, count in types.most_common():
            print(f"   {device_type}: {count}")
        
        # Показываем примеры
        print("\n🎯 Примеры найденного оборудования:")
        for i, device in enumerate(network_devices[:3]):
            print(f"{i+1}. IP: {device['ip']}")
            print(f"   Имя: {device['hostname'] or 'Нет'}")
            print(f"   Тип: {device['device_type']}")
            print(f"   Модель: {device['model'] or 'Не определена'}")
            if device['serial']:
                print(f"   Серийник: {device['serial']}")
            print()
    
    # Если не нашли сетевое оборудование
    if not network_devices:
        print("\n⚠️  Не найдено сетевое оборудование по SNMP.")
        print("   Возможные причины:")
        print("   1. SNMP не включен на оборудовании")
        print("   2. Настроен другой community (не public)")
        print("   3. Оборудование блокирует запросы (фаервол)")
        print("   4. В списке IP нет сетевого оборудования")

def quick_test():
    """Быстрый тест на ключевых IP"""
    print("\n⚡ Быстрый тест на шлюзах:")
    test_gateways = ['192.168.8.1', '192.168.9.1', '192.168.10.1', '192.168.11.1']
    
    for ip in test_gateways:
        print(f"Проверяю {ip}...", end=' ')
        try:
            device = get_device_info(ip, 'public')
            if device['success']:
                print(f"✅ {device['device_type']} - {device['hostname']}")
            else:
                print(f"❌ Не отвечает")
        except:
            print(f"❌ Ошибка")

if __name__ == "__main__":
    main()
    quick_test()  # Дополнительный тест на шлюзах