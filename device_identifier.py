# device_identifier.py
import socket
import json

def identify_device(ip):
    """Пытается определить тип устройства по открытым портам"""
    common_ports = {
        22: 'SSH (Linux/Network Device)',
        23: 'Telnet (Legacy Network)',
        80: 'HTTP (Web Server/Device)',
        443: 'HTTPS (Secure Web)',
        161: 'SNMP (Network Equipment)',
        3389: 'RDP (Windows)',
        21: 'FTP',
        25: 'SMTP',
        110: 'POP3',
        143: 'IMAP',
        445: 'SMB (Windows Share)',
        139: 'NetBIOS',
        53: 'DNS',
    }
    
    device_info = {
        'ip': ip,
        'hostname': None,
        'open_ports': [],
        'device_type': 'Unknown',
        'possible_types': []
    }
    
    # Пробуем получить имя хоста
    try:
        device_info['hostname'] = socket.gethostbyaddr(ip)[0]
    except:
        pass
    
    # Проверяем наиболее важные порты
    for port, description in common_ports.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Быстрая проверка
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                device_info['open_ports'].append(port)
                device_info['possible_types'].append(description)
        except:
            continue
    
    # Определяем тип устройства
    if 161 in device_info['open_ports']:
        device_info['device_type'] = 'Network Equipment (SNMP)'
    elif 22 in device_info['open_ports']:
        device_info['device_type'] = 'Linux/Network Device (SSH)'
    elif 3389 in device_info['open_ports']:
        device_info['device_type'] = 'Windows Machine'
    elif 80 in device_info['open_ports'] or 443 in device_info['open_ports']:
        device_info['device_type'] = 'Web Server/Device'
    elif 445 in device_info['open_ports'] or 139 in device_info['open_ports']:
        device_info['device_type'] = 'Windows File Server'
    
    return device_info

def main():
    print("🔍 Идентификация сетевых устройств")
    print("=" * 40)
    
    # Читаем найденные IP из файла
    try:
        with open('active_hosts.txt', 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Файл active_hosts.txt не найден. Сначала запустите сканирование.")
        return
    
    print(f"📋 Всего IP для проверки: {len(ips)}")
    print("\nНачинаем идентификацию...\n")
    
    devices = []
    
    # Проверяем каждое устройство (можно ограничить для теста)
    test_ips = ips[:10]  # Первые 10 для теста
    
    for ip in test_ips:
        print(f"Проверяем {ip}...", end=' ')
        device = identify_device(ip)
        devices.append(device)
        print(f"тип: {device['device_type']}")
    
    # Сохраняем результаты
    with open('identified_devices.json', 'w', encoding='utf-8') as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в 'identified_devices.json'")
    
    # Статистика
    types = {}
    for d in devices:
        t = d['device_type']
        types[t] = types.get(t, 0) + 1
    
    print("\n📊 Статистика по типам:")
    for t, count in types.items():
        print(f"  {t}: {count}")

if __name__ == "__main__":
    main()