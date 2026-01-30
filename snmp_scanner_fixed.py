# snmp_scanner_fixed.py
from pysnmp.hlapi import *
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

def snmp_get(ip, oid, community='public'):
    """Простой SNMP GET запрос"""
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community, mpModel=1),
                   UdpTransportTarget((ip, 161), timeout=2, retries=1),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        
        if errorIndication or errorStatus:
            return None
        else:
            return str(varBinds[0][1]) if varBinds else None
    except Exception as e:
        return None

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
    
    # Основные OID для запроса
    oids = {
        'description': '1.3.6.1.2.1.1.1.0',
        'hostname': '1.3.6.1.2.1.1.5.0',
        'location': '1.3.6.1.2.1.1.6.0',
        'uptime': '1.3.6.1.2.1.1.3.0'
    }
    
    try:
        # Запрашиваем все OID разом
        results = {}
        for key, oid in oids.items():
            value = snmp_get(ip, oid, community)
            if value:
                results[key] = value
        
        if not results.get('description'):
            device['error'] = 'Нет ответа на SNMP'
            return device
        
        device['success'] = True
        device['description'] = results.get('description', '')
        device['hostname'] = results.get('hostname')
        device['location'] = results.get('location')
        device['uptime'] = results.get('uptime')
        
        # Определяем тип устройства
        desc_lower = device['description'].lower()
        if 'cisco' in desc_lower:
            device['device_type'] = 'Cisco Switch/Router'
            # Серийник для Cisco
            serial = snmp_get(ip, '1.3.6.1.4.1.9.3.6.3.0', community)
            if serial:
                device['serial'] = serial
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
        
        # Извлекаем модель из описания
        if device['description']:
            model_patterns = [
                r'(WS-[A-Z]\d+[A-Z]?\d*)',
                r'(Catalyst\s+\S+)',
                r'(SG\d+)',
                r'(SRW\d+)',
                r'(DES-\d+)',
                r'(\b\d+[A-Z]+\d+\b)',
            ]
            
            for pattern in model_patterns:
                match = re.search(pattern, device['description'], re.IGNORECASE)
                if match:
                    device['model'] = match.group(1)
                    break
            
            if not device['model']:
                words = device['description'].split()[:2]
                device['model'] = ' '.join(words) if words else 'Unknown'
        
    except Exception as e:
        device['error'] = str(e)
    
    return device

def main():
    print("🔍 SNMP Scanner для сетевого оборудования")
    print("=" * 50)
    
    # Читаем найденные IP
    try:
        with open('active_hosts.txt', 'r') as f:
            all_ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Файл active_hosts.txt не найден")
        print("   Сначала запусти: python network_scanner.py")
        return
    
    print(f"📋 Всего IP для проверки: {len(all_ips)}")
    
    # Берем первые 20 для теста
    test_ips = all_ips[:20]
    print(f"🔬 Проверяем первые {len(test_ips)} устройств...\n")
    
    devices = []
    successful = 0
    
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
                name = device['hostname'] or 'Без имени'
                print(f"{symbol} {ip}: {name} - {device['device_type']}")
            else:
                print(f"❌ {ip}: Не отвечает на SNMP")
    
    # Фильтруем успешные
    network_devices = [d for d in devices if d['success']]
    
    print(f"\n📊 Результаты за {time.time() - start_time:.1f}с:")
    print(f"   Всего проверено: {len(devices)}")
    print(f"   Ответили на SNMP: {successful}")
    
    if network_devices:
        with open('network_equipment.json', 'w', encoding='utf-8') as f:
            json.dump(network_devices, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в 'network_equipment.json'")
        
        # Показываем пример
        print("\n🎯 Примеры найденного:")
        for i, device in enumerate(network_devices[:3]):
            print(f"{i+1}. IP: {device['ip']}")
            print(f"   Имя: {device['hostname'] or 'Нет'}")
            print(f"   Тип: {device['device_type']}")
            print(f"   Модель: {device.get('model', 'Не определена')}")
            if device.get('serial'):
                print(f"   Серийник: {device['serial']}")
            print()
    
    else:
        print("\n⚠️  Сетевое оборудование не найдено.")
        print("   Проверь: ")
        print("   1. Установлен ли pysnmp-lextudio?")
        print("   2. Работает ли SNMP на оборудовании?")
        print("   3. Правильный ли community? (public)")

if __name__ == "__main__":
    main()