# network/services/scanner.py
import nmap
import socket
import subprocess
import platform
from datetime import datetime
import json
import re

class NetworkScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    def detect_network(self):
        """Определение локальной сети"""
        try:
            system = platform.system()
            
            if system == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IPv4' in line or 'IP Address' in line:
                        ip = line.split(':')[-1].strip()
                        if ip and not ip.startswith('169.254') and ip != '127.0.0.1':
                            parts = ip.split('.')
                            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            
            elif system in ["Linux", "Darwin"]:
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
                import re
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    ip = match.group(1)
                    if ip != '127.0.0.1':
                        parts = ip.split('.')
                        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except:
            pass
        
        return "192.168.10.0/24"
    
    def simple_scan(self, network="192.168.10.0/24"):
        """Простое сканирование сети для Django"""
        print(f"🔍 Запускаю сканирование сети: {network}")
        
        try:
            # Быстрое ping сканирование
            self.nm.scan(hosts=network, arguments='-sn -T4 --max-retries 1')
            
            devices = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    ip = host
                    mac = "не определен"
                    vendor = "не определен"
                    hostname = "не определен"
                    
                    # Получаем MAC адрес
                    if 'mac' in self.nm[host]['addresses']:
                        mac = self.nm[host]['addresses']['mac']
                    
                    # Получаем производителя
                    if 'vendor' in self.nm[host] and mac in self.nm[host]['vendor']:
                        vendor = self.nm[host]['vendor'][mac]
                    
                    # Пытаемся получить hostname
                    if 'hostnames' in self.nm[host] and self.nm[host]['hostnames']:
                        hostname = self.nm[host]['hostnames'][0].get('name', ip)
                    
                    # Определяем тип устройства
                    device_type = self.determine_device_type(ip, mac, vendor, hostname)
                    
                    # Генерируем понятное имя устройства
                    device_name = self._generate_device_name(device_type, vendor, hostname, ip)
                    
                    device = {
                        'ip': ip,
                        'mac': mac,
                        'manufacturer': vendor,
                        'hostname': hostname,
                        'device_type': device_type,
                        'device_name': device_name,
                        'status': 'up'
                    }
                    
                    devices.append(device)
                    print(f"✅ Найдено: {ip} ({device_type}) - {vendor}")
            
            print(f"📊 Всего найдено: {len(devices)} устройств")
            
            if not devices:
                # Если ничего не найдено, возвращаем тестовые данные для разработки
                devices = self._get_test_devices()
            
            return devices
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            # Возвращаем тестовые данные при ошибке
            return self._get_test_devices()
    
    def determine_device_type(self, ip, mac, vendor, hostname):
        """Определяет тип устройства по различным признакам"""
        vendor_lower = vendor.lower() if vendor else ""
        mac_upper = mac.upper() if mac else ""
        
        # По производителю
        if any(word in vendor_lower for word in ['giga-byte', 'micro-star', 'msi', 'asus', 'intel', 'acer', 'dell', 'lenovo', 'hp inc.', 'hewlett-packard', 'microsoft', 'samsung',
        'azurewave', 'realtek', 'broadcom']):
            return 'computer'
        elif any(word in vendor_lower for word in ['cisco', 'mikrotik', 'ubiquiti', 'tplink', 'd-link', 'zyxel', 'aruba', 'extreme', 'juniper']):
            return 'router'
        elif any(word in vendor_lower for word in ['hp inc.', 'hewlett-packard', 'hp printer', 'canon', 'epson', 'brother', 'kyocera', 'xerox']):
            return 'printer'
        elif any(word in vendor_lower for word in ['grandstream', 'yealink', 'polycom', 'avaya', 'snom', 'panasonic']):
            return 'voip_phone'        
        elif any(word in vendor_lower for word in ['hikvision', 'dahua', 'axis', 'bosch']):
            return 'camera'
        elif any(word in vendor_lower for word in ['samsung', 'apple', 'xiaomi', 'huawei', 'sony', 'lg']):
            return 'mobile'
        elif any(word in vendor_lower for word in ['raspberry', 'arduino', 'iot']):
            return 'iot'
        
        # По MAC OUI (первые 6 символов)
        network_ouis = [
            '00:1C:C0', '00:0C:29', '00:50:56',  # VMware
            '00:1B:21', '00:1C:42',              # Fortinet
            '00:1A:2B', '00:1C:0E',              # Cisco
            '4C:5E:0C', '00:0C:42',              # MikroTik
            '00:1E:65', '80:2A:A8',              # Ubiquiti
            '00:15:6D', '00:23:CD',              # TP-Link
            '00:17:9A', '00:21:91',              # D-Link
        ]
        
        printer_ouis = [
            '00:01:E6', '00:0E:7F', '00:12:79',  # HP
            '00:50:F1', '00:01:47',              # Canon
            '00:0C:6E', '00:0A:27',              # Epson
            '00:80:77', '00:05:02',              # Brother
            '00:09:6D', '00:0A:DE',              # Kyocera
        ]
        
        voip_ouis = [
            '00:0B:82', '00:13:6A',              # Grandstream
            '00:15:65', '00:1E:72',              # Yealink
            '00:04:13', '00:18:6B',              # Polycom
            '00:0A:D9', '00:07:7D',              # Avaya
        ]
        
        # Проверяем по OUI
        for oui in printer_ouis:
            if mac_upper.startswith(oui):
                return 'printer'
        
        for oui in voip_ouis:
            if mac_upper.startswith(oui):
                return 'voip_phone'
        
        for oui in network_ouis:
            if mac_upper.startswith(oui):
                return 'network_device'
        
        # По портам (если есть дополнительное сканирование)
        if self._check_ports(ip, [22, 23, 161]):  # SSH, Telnet, SNMP
            return 'network_device'
        elif self._check_ports(ip, [80, 443, 8080]):  # HTTP/HTTPS
            return 'web_device'
        
        return 'unknown'
    
    def _check_ports(self, ip, ports):
        """Быстрая проверка портов"""
        try:
            for port in ports[:3]:  # Проверяем только первые 3 порта
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result == 0:
                    return True
        except:
            pass
        return False
    
    def _generate_device_name(self, device_type, vendor, hostname, ip):
        """Генерирует понятное имя устройства"""
        # Словарь для перевода типов на русский
        type_translation = {
            'router': 'Роутер',
            'switch': 'Коммутатор',
            'printer': 'Принтер',
            'computer': 'Компьютер',
            'voip_phone': 'IP-телефон',
            'server': 'Сервер',
            'camera': 'Камера',
            'mobile': 'Мобильное устройство',
            'network_device': 'Сетевое оборудование',
            'web_device': 'Веб-устройство',
            'iot': 'IoT устройство',
            'unknown': 'Неизвестное устройство'
        }
        
        # Получаем русское название типа
        russian_type = type_translation.get(device_type, device_type)
        
        # Для компьютеров от Gigabyte, Micro-Star и т.д. - упрощаем название
        vendor_lower = vendor.lower() if vendor else ""
        
        if device_type == 'computer':
            # Если это компьютер от известного производителя материнских плат
            if any(brand in vendor_lower for brand in ['giga-byte', 'micro-star', 'asus', 'msi']):
                if hostname and hostname != ip and hostname != "не определен":
                    return f"Компьютер: {hostname}"
                else:
                    # Сокращаем название производителя
                    clean_vendor = vendor.replace('Technology', '').replace('Intl', '').replace('Corp.', '').strip()
                    return f"Компьютер ({clean_vendor})"
        
        # Для веб-устройств уточняем
        if device_type == 'web_device':
            if hostname and hostname != ip and hostname != "не определен":
                return f"Веб-интерфейс: {hostname}"
            elif vendor and vendor != "не определен":
                return f"Веб-устройство: {vendor}"
            else:
                return f"Веб-устройство ({ip})"
        
        # Используем hostname если он есть и не равен IP
        if hostname and hostname != ip and hostname != "не определен":
            return f"{russian_type}: {hostname}"
        
        # Используем производителя если он есть
        if vendor and vendor != "не определен":
            # Убираем лишние слова из названия производителя
            clean_vendor = vendor.replace('Inc.', '').replace('Corporation', '')\
                                .replace('LLC', '').replace('Technology', '')\
                                .replace('Intl', '').replace('GmbH', '').strip()
            return f"{russian_type}: {clean_vendor}"
        
        # Если ничего нет, используем IP
        return f"{russian_type} ({ip})"
    
    def perform_scan(self, network=None):
        """Основной метод сканирования для Django views"""
        if not network:
            network = self.detect_network()
        
        return self.simple_scan(network)
    
    def _get_test_devices(self):
        """Тестовые данные для разработки"""
        print("⚠️ Использую тестовые данные")
        return [
            {
                'ip': '192.168.10.1',
                'mac': '00:1A:2B:3C:4D:5E',
                'manufacturer': 'MikroTik',
                'hostname': 'router-main',
                'device_type': 'router',
                'device_name': 'Роутер: MikroTik',
                'status': 'up'
            },
            {
                'ip': '192.168.10.11',
                'mac': 'C0:74:AD:40:BF:9B',
                'manufacturer': 'Grandstream Networks',
                'hostname': 'sip-phone-11',
                'device_type': 'voip_phone',
                'device_name': 'IP-телефон: Grandstream',
                'status': 'up'
            },
            {
                'ip': '192.168.10.100',
                'mac': '00:11:22:33:44:55',
                'manufacturer': 'HP Inc.',
                'hostname': 'workstation-100',
                'device_type': 'computer',
                'device_name': 'Компьютер: workstation-100',
                'status': 'up'
            },
            {
                'ip': '192.168.10.110',
                'mac': '7C:4D:8F:86:6F:38',
                'manufacturer': 'HP Printer',
                'hostname': 'office-printer',
                'device_type': 'printer',
                'device_name': 'Принтер: HP',
                'status': 'up'
            },
            {
                'ip': '192.168.10.200',
                'mac': '08:00:27:AA:BB:CC',
                'manufacturer': 'PCS Systemtechnik GmbH',
                'hostname': 'server-200',
                'device_type': 'server',
                'device_name': 'Сервер: server-200',
                'status': 'up'
            }
        ]

# Создаем глобальный экземпляр сканера
scanner = NetworkScanner()