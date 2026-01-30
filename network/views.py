# network/views.py
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.generic import ListView, DetailView, TemplateView, View
from .models import Location, NetworkEquipment, Subnet, IPAddress
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages

# ============================================================================
# МИКСИНЫ
# ============================================================================

class AdminRequiredMixin(LoginRequiredMixin):
    """Миксин для страниц, требующих админ-прав"""
    login_url = '/admin/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            next_url = request.get_full_path()
            return redirect(f'/admin/login/?next={next_url}')
        return super().dispatch(request, *args, **kwargs)

# ============================================================================
# ИМПОРТ СКАНЕРА
# ============================================================================

try:
    from .services.scanner import scanner
    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False
    # Заглушка если скрипта нет
    class DummyScanner:
        def detect_network(self):
            return "192.168.10.0/24"
        def perform_scan(self, network):
            return [{
                'ip': '192.168.10.1', 
                'mac': '00:11:22:33:44:55', 
                'manufacturer': 'Тестовый производитель', 
                'hostname': 'test-device'
            }]
    
    scanner = DummyScanner()

# ============================================================================
# ОСНОВНЫЕ СТРАНИЦЫ
# ============================================================================

class EquipmentListView(AdminRequiredMixin, ListView):
    """СПИСОК ОБОРУДОВАНИЯ"""
    model = NetworkEquipment
    template_name = 'network/equipment_list.html'
    context_object_name = 'equipments'
    
    def get_queryset(self):
        queryset = NetworkEquipment.objects.all()
        
        # Фильтрация по статусу
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(serial_number__icontains=search_query) |
                Q(inventory_number__icontains=search_query) |
                Q(ip_address__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика
        context['status_stats'] = {
            'active': NetworkEquipment.objects.filter(status='active').count(),
            'backup': NetworkEquipment.objects.filter(status='backup').count(),
            'repair': NetworkEquipment.objects.filter(status='repair').count(),
            'decommissioned': NetworkEquipment.objects.filter(status='decommissioned').count(),
        }
        
        # Параметры фильтров
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


class EquipmentDetailView(DetailView):
    """ДЕТАЛИ ОБОРУДОВАНИЯ"""
    model = NetworkEquipment
    template_name = 'network/equipment_detail.html'
    context_object_name = 'equipment'


class SubnetListView(ListView):
    """СПИСОК ПОДСЕТЕЙ"""
    model = Subnet
    template_name = 'network/subnet_list.html'
    context_object_name = 'subnets'
    
    def get_queryset(self):
        return Subnet.objects.all().select_related('location')


class SubnetDetailView(DetailView):
    """ДЕТАЛИ ПОДСЕТИ + IP АДРЕСА"""
    model = Subnet
    template_name = 'network/subnet_detail.html'
    context_object_name = 'subnet'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subnet = self.object
        
        # Все IP адреса в подсети
        ip_addresses = IPAddress.objects.filter(
            subnet=subnet
        ).select_related('device')
        
        # Вычисляем свободные IP
        all_ips = list(subnet.get_ip_range())
        used_ips = [ip.address for ip in ip_addresses]
        free_ips = [ip for ip in all_ips if ip not in used_ips]
        
        context.update({
            'ip_addresses': ip_addresses,
            'free_ips': free_ips[:50],
            'free_count': len(free_ips),
            'used_count': len(used_ips),
            'total_count': len(all_ips),
        })
        
        return context


class NetworkMapView(AdminRequiredMixin, TemplateView):
    """КАРТА СЕТИ"""
    template_name = 'network/network_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        devices = NetworkEquipment.objects.all().select_related('location')
        
        # Данные для векторной схемы
        network_nodes = []
        network_edges = []
        
        # 1. Создаем узлы (устройства)
        for device in devices:
            network_nodes.append({
                'id': device.id,
                'label': f"{device.name}\n{device.ip_address or '-'}",
                'group': device.type or 'other',
                'title': f"{device.name}",
                'url': reverse('network:equipment_detail', args=[device.id]),
            })
        
        # 2. СОЗДАЕМ СВЯЗИ (edges) - ключевое!
        
        # Вариант A: Связь роутер ↔ все устройства в его подсети
        routers = [d for d in devices if d.type == 'router' and d.ip_address]
        for router in routers:
            router_ip_parts = router.ip_address.split('.')
            router_subnet = f"{router_ip_parts[0]}.{router_ip_parts[1]}.{router_ip_parts[2]}."
            
            for device in devices:
                if (device.id != router.id and 
                    device.ip_address and 
                    device.ip_address.startswith(router_subnet)):
                    
                    network_edges.append({
                        'from': router.id,
                        'to': device.id,
                        'label': 'LAN',
                        'color': {'color': '#3498db'},
                        'arrows': 'to'
                    })
        
        # Вариант B: Связь по локациям
        devices_by_location = {}
        for device in devices:
            if device.location_id:
                loc_id = device.location_id
                if loc_id not in devices_by_location:
                    devices_by_location[loc_id] = []
                devices_by_location[loc_id].append(device.id)
        
        # Связываем устройства в одном помещении
        for location_id, device_ids in devices_by_location.items():
            if len(device_ids) > 1:
                # Создаем "хаб" для локации
                for i in range(len(device_ids) - 1):
                    for j in range(i + 1, len(device_ids)):
                        network_edges.append({
                            'from': device_ids[i],
                            'to': device_ids[j],
                            'label': 'локация',
                            'color': {'color': '#95a5a6'},
                            'dashes': True
                        })
        
        # Вариант C: Иерархия по типам (если нет сетевых данных)
        if not network_edges and devices:
            # Простая древовидная структура
            network_devices = [d for d in devices if d.type in ['router', 'switch', 'firewall']]
            other_devices = [d for d in devices if d.type not in ['router', 'switch', 'firewall']]
            
            if network_devices:
                main_device = network_devices[0]
                for device in other_devices:
                    if device.id != main_device.id:
                        network_edges.append({
                            'from': main_device.id,
                            'to': device.id,
                            'label': 'сеть'
                        })
        
        context['network_nodes_json'] = json.dumps(network_nodes, ensure_ascii=False)
        context['network_edges_json'] = json.dumps(network_edges, ensure_ascii=False)  # <-- ДОБАВЛЕНО
        context['devices'] = devices
        context['all_locations'] = Location.objects.all()
        
        # Для отладки
        print(f"🔗 Узлов: {len(network_nodes)}, Связей: {len(network_edges)}")
        
        return context
        

class IPManagementView(AdminRequiredMixin, TemplateView):
    """УПРАВЛЕНИЕ IP-АДРЕСАМИ"""
    template_name = 'network/ip_management.html'
    
    def _get_ip_stats(self):
        """Вспомогательный метод для статистики IP"""
        subnets = Subnet.objects.all().prefetch_related('ipaddress_set')
        stats = []
        
        for subnet in subnets:
            total_ips = subnet.get_ip_count()
            used_ips = subnet.ipaddress_set.count()
            free_ips = total_ips - used_ips
            
            stats.append({
                'subnet': subnet,
                'cidr': f"{subnet.network_address}/{subnet.prefix_length}",
                'total': total_ips,
                'used': used_ips,
                'free': free_ips,
                'usage_percent': (used_ips / total_ips * 100) if total_ips > 0 else 0
            })
        
        return stats
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'ip_stats': self._get_ip_stats(),
            'total_subnets': Subnet.objects.count(),
            'search_ip': self.request.GET.get('search_ip', '')
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """ПОИСК IP АДРЕСА"""
        ip = request.POST.get('search_ip', '').strip()
        if not ip:
            messages.warning(request, 'Введите IP адрес для поиска')
            return redirect('network:ip_management')
        
        context = self.get_context_data()
        context['search_ip'] = ip
        
        try:
            # Проверяем в IPAddress
            ip_address = IPAddress.objects.filter(address=ip).select_related('device', 'subnet').first()
            
            if ip_address:
                context['ip_result'] = ip_address
            else:
                # Если не найдено в IPAddress, проверяем в NetworkEquipment
                equipment = NetworkEquipment.objects.filter(
                    Q(ip_address=ip) | Q(management_ip=ip)
                ).first()
                if equipment:
                    context['equipment_result'] = equipment
                else:
                    messages.info(request, f'IP адрес {ip} не найден в базе')
        
        except Exception as e:
            messages.error(request, f'Ошибка при поиске IP: {str(e)}')
        
        return render(request, self.template_name, context)

# ============================================================================
# СКАНЕР СЕТИ
# ============================================================================

class NetworkScannerView(AdminRequiredMixin, TemplateView):
    """СТРАНИЦА СКАНЕРА СЕТИ"""
    template_name = 'network/scanner.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            detected_network = scanner.detect_network()
        except Exception as e:
            detected_network = "192.168.10.0/24"
        
        context.update({
            'detected_network': detected_network,
            'scanner_available': SCANNER_AVAILABLE,
            'scanning': False
        })
        
        return context


# network/views.py
class ScanResultsView(AdminRequiredMixin, View):
    """РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ СЕТИ"""
    
    def get(self, request, *args, **kwargs):
        network = request.GET.get('network', '').strip()  # GET параметр
        if not network:
            try:
                network = scanner.detect_network()
            except:
                network = "192.168.10.0/24"
        
        print(f"🔍 Запрашиваю сканирование сети: {network}")
        
        try:
            # Получаем устройства через сканер
            raw_devices = scanner.perform_scan(network)
            
            print(f"✅ Получено устройств: {len(raw_devices)}")
            
            processed_devices = []
            for device_data in raw_devices:
                if not isinstance(device_data, dict):
                    continue
                    
                ip = device_data.get('ip', '')
                if not ip:
                    continue
                
                mac = device_data.get('mac', 'не определен')
                manufacturer = device_data.get('manufacturer', 'не определен')
                hostname = device_data.get('hostname', ip)
                device_type = device_data.get('device_type', 'unknown')
                device_name = device_data.get('device_name', f"Устройство {ip}")
                
                # Проверяем в базе данных
                existing_device = None
                if ip:
                    existing_device = NetworkEquipment.objects.filter(ip_address=ip).first()
                if not existing_device and mac and mac != 'не определен':
                    existing_device = NetworkEquipment.objects.filter(mac_address=mac).first()
                
                # Преобразуем объект в словарь для шаблона
                existing_dict = None
                if existing_device:
                    existing_dict = {
                        'id': existing_device.id,
                        'name': existing_device.name,
                        'type': existing_device.type,
                        'model': existing_device.model,
                        'status': existing_device.status,
                    }
                
                processed_devices.append({
                    'ip': ip,
                    'mac': mac,
                    'manufacturer': manufacturer,
                    'hostname': hostname,
                    'device_type': device_type,
                    'device_name': device_name,
                    'in_database': bool(existing_device),
                    'existing_device': existing_dict
                })
        
        except Exception as e:
            print(f"❌ Ошибка в ScanResultsView: {e}")
            import traceback
            traceback.print_exc()
            processed_devices = []
            messages.error(request, f'Ошибка сканирования: {str(e)}')
        
        # Сохраняем в сессии
        request.session['scan_results'] = {
            'devices': processed_devices,
            'network': network,
            'total': len(processed_devices),
            'timestamp': timezone.now().isoformat()
        }
        
        # Статистика
        new_count = sum(1 for d in processed_devices if not d['in_database'])
        existing_count = len(processed_devices) - new_count
        
        context = {
            'devices': processed_devices,
            'network': network,
            'total': len(processed_devices),
            'new_count': new_count,
            'existing_count': existing_count,
            'timestamp': timezone.now(),
            'scanner_available': True,
        }
        
        return render(request, 'network/scan_results.html', context)
    
    # УДАЛИТЕ этот POST-метод или сделайте так:
    def post(self, request, *args, **kwargs):
        """Альтернатива: обрабатываем POST и перенаправляем на GET"""
        network = request.POST.get('network', '').strip()
        if not network:
            messages.warning(request, 'Введите сеть для сканирования')
            return redirect('network:scanner')
        
        return redirect(f'{reverse("network:scan_results")}?network={network}')        

class AddDeviceView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        print("="*50)
        print("📥 AddDeviceView вызван")
        
        ip = request.POST.get('ip', '').strip()
        mac = request.POST.get('mac', '').strip()
        manufacturer = request.POST.get('manufacturer', '').strip()
        hostname = request.POST.get('hostname', '').strip()
        
        print(f"📥 Данные: IP={ip}, MAC={mac}, Manufacturer={manufacturer}")
        
        if not ip:
            messages.error(request, 'Не указан IP адрес')
            return redirect('network:scan_results')
        
        # Проверяем, нет ли уже в базе
        if NetworkEquipment.objects.filter(ip_address=ip).exists():
            messages.warning(request, f'Устройство {ip} уже есть в базе')
            return redirect('network:scan_results')
        
        try:
            # ИСПРАВЛЕННОЕ ОПРЕДЕЛЕНИЕ ТИПА
            device_type = 'unknown'
            man_lower = str(manufacturer).lower()
            
            if 'giga-byte' in man_lower or 'gigabyte' in man_lower:
                device_type = 'computer'
            elif 'azurewave' in man_lower:
                device_type = 'computer'
            elif 'micro-star' in man_lower:
                device_type = 'computer'
            elif 'intel' in man_lower:
                device_type = 'computer'
            elif 'realtek' in man_lower:
                device_type = 'computer'
            elif 'cisco' in man_lower:
                device_type = 'router' if 'router' in man_lower else 'switch'
            elif 'mikrotik' in man_lower:
                device_type = 'router'
            elif 'ubiquiti' in man_lower:
                device_type = 'access_point'
            elif 'hp' in man_lower:
                device_type = 'printer' if 'printer' in man_lower or 'laserjet' in man_lower else 'server'
            elif 'kyocera' in man_lower:
                device_type = 'printer'
            elif 'd-link' in man_lower or 'tp-link' in man_lower:
                device_type = 'switch'
            elif 'grandstream' in man_lower:
                device_type = 'voip_phone'
            elif 'dahua' in man_lower or 'hikvision' in man_lower:
                device_type = 'camera'
            
            # ИСПРАВЛЕННОЕ ИМЯ
            name = ''
            if hostname and hostname != ip:
                name = hostname
            elif manufacturer and manufacturer != "не определен":
                name = f"{manufacturer} ({ip})"
            else:
                name = f"Устройство {ip}"
            
            # ОЧИСТКА MAC
            mac_clean = None
            if mac and mac != 'не определен' and len(mac) >= 12:
                mac_clean = mac
            
            # ОЧИСТКА ПРОИЗВОДИТЕЛЯ
            manufacturer_clean = None
            if manufacturer and manufacturer != 'не определен':
                manufacturer_clean = manufacturer
            
            # Создаем устройство
            device = NetworkEquipment.objects.create(
                name=name,
                type=device_type,
                ip_address=ip,
                mac_address=mac_clean,
                manufacturer=manufacturer_clean,
                status='active',
                scan_source='scanner'
            )
            
            print(f"📥 Создано устройство: {name} (тип: {device_type})")
            
            messages.success(request, f'Устройство {ip} добавлено в базу')
            return redirect('network:equipment_detail', pk=device.id)
            
        except Exception as e:
            print(f"❌ Ошибка в AddDeviceView: {str(e)}")
            messages.error(request, f'Ошибка при добавлении устройства: {str(e)}')
            return redirect('network:scan_results')


class BulkAddDevicesView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        print("="*50)
        print("📦 BulkAddDevicesView вызван")
        
        selected_ips = request.POST.getlist('selected_devices')
        scan_results = request.session.get('scan_results', {}).get('devices', [])
        
        print(f"📦 Выбрано IP: {selected_ips}")
        print(f"📦 Устройств в сессии: {len(scan_results)}")
        
        if not selected_ips:
            messages.warning(request, 'Не выбрано ни одного устройства')
            return redirect('network:scan_results')
        
        added = 0
        skipped = 0
        errors = 0
        
        devices_to_create = []
        
        for device_data in scan_results:
            if device_data['ip'] in selected_ips:
                ip = device_data['ip']
                
                # Проверяем, нет ли уже в базе
                if NetworkEquipment.objects.filter(ip_address=ip).exists():
                    skipped += 1
                    continue
                
                try:
                    # ДАННЫЕ ИЗ СКАНЕРА
                    mac = device_data.get('mac', '')
                    manufacturer = device_data.get('manufacturer', '')
                    hostname = device_data.get('hostname', '')
                    device_type_scanner = device_data.get('device_type', '')
                    device_name_scanner = device_data.get('device_name', '')
                    
                    # 1. ИСПРАВЛЯЕМ НАЗВАНИЕ
                    name = ''
                    if device_name_scanner and device_name_scanner != ip:
                        name = device_name_scanner
                    elif hostname and hostname != ip:
                        name = hostname
                    elif manufacturer and manufacturer != "не определен":
                        name = f"{manufacturer} ({ip})"
                    else:
                        name = f"Устройство {ip}"
                    
                    # 2. ИСПРАВЛЯЕМ ТИП УСТРОЙСТВА
                    device_type = 'unknown'
                    man_lower = str(manufacturer).lower()
                    
                    if 'giga-byte' in man_lower or 'gigabyte' in man_lower:
                        device_type = 'computer'
                    elif 'azurewave' in man_lower:
                        device_type = 'computer'
                    elif 'micro-star' in man_lower:
                        device_type = 'computer'
                    elif 'intel' in man_lower:
                        device_type = 'computer'
                    elif 'realtek' in man_lower:
                        device_type = 'computer'
                    elif 'cisco' in man_lower:
                        device_type = 'router' if 'router' in man_lower else 'switch'
                    elif 'mikrotik' in man_lower:
                        device_type = 'router'
                    elif 'ubiquiti' in man_lower:
                        device_type = 'access_point'
                    elif 'hp' in man_lower:
                        device_type = 'printer' if 'printer' in man_lower or 'laserjet' in man_lower else 'server'
                    elif 'kyocera' in man_lower:
                        device_type = 'printer'
                    elif 'd-link' in man_lower or 'tp-link' in man_lower:
                        device_type = 'switch'
                    elif 'grandstream' in man_lower:
                        device_type = 'voip_phone'
                    elif 'dahua' in man_lower or 'hikvision' in man_lower:
                        device_type = 'camera'
                    
                    # Если из сканера уже пришел тип
                    if device_type_scanner and device_type_scanner != 'unknown':
                        device_type = device_type_scanner
                    
                    # 3. ОБРАБАТЫВАЕМ MAC И ПРОИЗВОДИТЕЛЯ
                    mac_clean = None
                    if mac and mac != 'не определен' and len(mac) >= 12:
                        mac_clean = mac
                    
                    manufacturer_clean = None
                    if manufacturer and manufacturer != 'не определен':
                        manufacturer_clean = manufacturer
                    
                    # 4. СОЗДАЕМ УСТРОЙСТВО
                    devices_to_create.append(
                        NetworkEquipment(
                            name=name,
                            type=device_type,
                            ip_address=ip,
                            mac_address=mac_clean,
                            manufacturer=manufacturer_clean,
                            status='active',
                            scan_source='scanner'
                        )
                    )
                    
                    print(f"📦 Подготовлено: {name} ({ip}) - тип: {device_type}")
                    
                except Exception as e:
                    errors += 1
                    print(f"❌ Ошибка обработки устройства {ip}: {str(e)}")
                    messages.error(request, f'Ошибка обработки устройства {ip}: {str(e)}')
        
        # Массовое создание
        if devices_to_create:
            try:
                NetworkEquipment.objects.bulk_create(devices_to_create)
                added = len(devices_to_create)
                print(f"✅ Добавлено устройств: {added}")
            except Exception as e:
                print(f"❌ Ошибка при массовом добавлении: {str(e)}")
                messages.error(request, f'Ошибка при массовом добавлении: {str(e)}')
        
        # Результат
        if added:
            messages.success(request, f'Успешно добавлено {added} устройств')
        if skipped:
            messages.info(request, f'{skipped} устройств уже были в базе и пропущены')
        if errors:
            messages.error(request, f'При обработке {errors} устройств возникли ошибки')
        
        return redirect('network:equipment_list')