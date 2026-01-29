# network/services/scanner.py
import nmap
import subprocess
import platform
from django.utils import timezone
import json

class NetworkScanner:
    """Улучшенный сканер сети - работает как network_scanner.py"""
    
    def __init__(self):
        self.nm = nmap.PortScanner()
    
    def detect_network(self):
        """Автоопределение сети"""
        system = platform.system()
        
        if system == "Windows":
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp866')
                for line in result.stdout.split('\n'):
                    if 'IPv4' in line or 'IP Address' in line:
                        if ':' in line:
                            ip = line.split(':')[-1].strip()
                            if ip and not ip.startswith('169.254') and ip != '127.0.0.1':
                                parts = ip.split('.')
                                if len(parts) == 4:
                                    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            except:
                pass
        
        return "192.168.10.0/24"
    
    def perform_scan(self, network_cidr="192.168.10.0/24"):
        """Выполнить сканирование КАК В network_scanner.py"""
        print(f"🔍 Сканирую сеть: {network_cidr}")
        
        try:
            # ИСПОЛЬЗУЕМ ТЕ ЖЕ АРГУМЕНТЫ, ЧТО И В network_scanner.py
            self.nm.scan(hosts=network_cidr, arguments='-sn -T4 --max-retries 1')
            
            devices = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    device = {
                        'ip': host,
                        'mac': 'не определен',
                        'manufacturer': 'не определен',
                        'hostname': host,
                        'status': 'up'
                    }
                    
                    # Пытаемся получить MAC - ИСПРАВЛЕННЫЙ КОД
                    try:
                        if 'addresses' in self.nm[host]:
                            # Пробуем разные варианты ключей для MAC
                            for key in ['mac', 'addr', 'address']:
                                if key in self.nm[host]['addresses']:
                                    device['mac'] = self.nm[host]['addresses'][key]
                                    break
                            
                            # Производитель из vendor
                            if 'vendor' in self.nm[host]:
                                # Пробуем найти vendor по MAC
                                mac_keys = [k for k in self.nm[host]['vendor'].keys() 
                                           if 'mac' in k.lower() or device['mac'] in k]
                                if mac_keys:
                                    device['manufacturer'] = self.nm[host]['vendor'][mac_keys[0]]
                    
                    except Exception as e:
                        print(f"Ошибка при получении MAC для {host}: {e}")
                    
                    # Hostname
                    try:
                        if 'hostnames' in self.nm[host] and self.nm[host]['hostnames']:
                            for hostname in self.nm[host]['hostnames']:
                                if hostname.get('name') and hostname['name'] != host:
                                    device['hostname'] = hostname['name']
                                    break
                    except:
                        pass
                    
                    devices.append(device)
            
            print(f"✅ Найдено устройств: {len(devices)}")
            
            # Сохраняем в файл для отладки
            self._debug_save(devices, network_cidr)
            
            return devices
            
        except Exception as e:
            print(f"❌ Ошибка сканирования: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _debug_save(self, devices, network):
        """Сохранение результатов для отладки"""
        debug_data = {
            'network': network,
            'total': len(devices),
            'devices': devices,
            'timestamp': timezone.now().isoformat()
        }
        
        try:
            with open('network_scan_debug.json', 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("💾 Результаты сохранены в network_scan_debug.json")
        except:
            pass

# Глобальный экземпляр
scanner = NetworkScanner()