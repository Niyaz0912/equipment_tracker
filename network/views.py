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
except ImportError:
    # Если сервис еще не создан, создаем заглушку
    class DummyScanner:
        def detect_network(self):
            return "192.168.10.0/24"
        def perform_scan(self, network):
            return []
    
    scanner = DummyScanner()

# ============================================================================
# ОСНОВНЫЕ VIEW
# ============================================================================

class EquipmentListView(AdminRequiredMixin, ListView):
    """Список оборудования + сканер на вкладке"""
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
        
        # Данные для вкладки сканера
        context['detected_network'] = scanner.detect_network()
        context['last_scan'] = self.request.session.get('network_scan_results', {})
        
        # Параметры фильтров
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Обработка сканирования сети"""
        network = request.POST.get('network', scanner.detect_network())
        
        # Запускаем сканирование
        devices = scanner.perform_scan(network)
        
        # Сохраняем в сессии
        request.session['network_scan_results'] = {
            'devices': devices,
            'network': network,
            'timestamp': timezone.now().isoformat(),
            'total': len(devices)
        }
        
        messages.success(
            request, 
            f'Найдено {len(devices)} устройств в сети {network}'
        )
        
        return redirect('network:equipment_list')


class EquipmentDetailView(DetailView):
    """Детали оборудования"""
    model = NetworkEquipment
    template_name = 'network/equipment_detail.html'
    context_object_name = 'equipment'


class SubnetListView(ListView):
    """Список всех подсетей"""
    model = Subnet
    template_name = 'network/subnet_list.html'
    context_object_name = 'subnets'
    
    def get_queryset(self):
        return Subnet.objects.all().select_related('location')


class SubnetDetailView(DetailView):
    """Детали подсети + IP адреса"""
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
            'free_ips': free_ips[:50],  # Показываем первые 50 свободных
            'free_count': len(free_ips),
            'used_count': len(used_ips),
            'total_count': len(all_ips),
        })
        
        return context


class NetworkMapView(AdminRequiredMixin, TemplateView):
    """Карта сети с двумя режимами просмотра"""
    template_name = 'network/network_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Параметры
        view_mode = self.request.GET.get('mode', 'vector')  # 'vector' или 'location'
        location_filter = self.request.GET.get('location')
        type_filter = self.request.GET.get('type')
        
        # Получаем оборудование
        devices = NetworkEquipment.objects.all().select_related('location')
        
        # Применяем фильтры
        if location_filter:
            devices = devices.filter(location_id=location_filter)
        if type_filter:
            devices = devices.filter(type=type_filter)
        
        # Данные для векторной схемы
        if view_mode == 'vector':
            network_nodes = []
            for device in devices:
                network_nodes.append({
                    'id': device.id,
                    'label': f"{device.name}\n{device.ip_address or '-'}",
                    'group': device.type or 'other',
                    'title': f"{device.name}",
                    'url': reverse('network:equipment_detail', args=[device.id]),
                })
            context['network_nodes_json'] = json.dumps(network_nodes, ensure_ascii=False)
        
        # Данные для карты по локациям
        elif view_mode == 'location':
            locations_data = {}
            for device in devices:
                location_id = device.location_id if device.location else 0
                if location_id not in locations_data:
                    locations_data[location_id] = {
                        'location': device.location,
                        'devices': []
                    }
                locations_data[location_id]['devices'].append(device)
            context['locations_data'] = list(locations_data.values())
        
        # Общие данные
        context.update({
            'view_mode': view_mode,
            'devices': devices,
            'all_locations': Location.objects.all(),
            'device_count': devices.count(),
        })
        
        return context


class IPManagementView(AdminRequiredMixin, TemplateView):
    """IP-менеджмент (замена поиску IP)"""
    template_name = 'network/ip_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика по IP
        subnets = Subnet.objects.all().prefetch_related('ipaddress_set')
        
        ip_stats = []
        for subnet in subnets:
            total_ips = subnet.get_ip_count()
            used_ips = subnet.ipaddress_set.count()
            free_ips = total_ips - used_ips
            
            ip_stats.append({
                'subnet': subnet,
                'cidr': f"{subnet.network_address}/{subnet.prefix_length}",
                'total': total_ips,
                'used': used_ips,
                'free': free_ips,
                'usage_percent': (used_ips / total_ips * 100) if total_ips > 0 else 0
            })
        
        context.update({
            'ip_stats': ip_stats,
            'total_subnets': len(subnets),
            'search_ip': self.request.GET.get('search_ip', '')
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Поиск IP адреса"""
        ip = request.POST.get('search_ip', '').strip()
        if ip:
            # Проверяем в IPAddress
            ip_address = IPAddress.objects.filter(address=ip).select_related('device', 'subnet').first()
            
            # Если не найдено в IPAddress, проверяем в NetworkEquipment
            if not ip_address:
                equipment = NetworkEquipment.objects.filter(ip_address=ip).first()
                if equipment:
                    return render(request, 'network/ip_management.html', {
                        'search_ip': ip,
                        'equipment_result': equipment,
                        'ip_stats': []  # Добавить логику получения статистики
                    })
            
            return render(request, 'network/ip_management.html', {
                'search_ip': ip,
                'ip_result': ip_address,
                'ip_stats': []  # Добавить логику получения статистики
            })
        
        return redirect('network:ip_management')


# ============================================================================
# API VIEW ДЛЯ СКАНИРОВАНИЯ И ДОБАВЛЕНИЯ
# ============================================================================

class ScanDevicesAPIView(AdminRequiredMixin, View):
    """API для сканирования устройств (AJAX)"""
    
    def post(self, request, *args, **kwargs):
        network = request.POST.get('network', scanner.detect_network())
        
        try:
            # Запускаем сканирование
            devices = scanner.perform_scan(network)
            
            # Сохраняем в сессии
            request.session['network_scan_results'] = {
                'devices': devices,
                'network': network,
                'timestamp': timezone.now().isoformat(),
                'total': len(devices)
            }
            
            return JsonResponse({
                'success': True,
                'count': len(devices),
                'network': network,
                'devices': devices[:10]  # Возвращаем первые 10 для предпросмотра
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class GetScanResultsAPIView(AdminRequiredMixin, View):
    """API для получения результатов сканирования"""
    
    def get(self, request, *args, **kwargs):
        scan_data = request.session.get('network_scan_results', {})
        devices = scan_data.get('devices', [])
        
        # Сравниваем с базой
        devices_with_status = []
        new_count = 0
        existing_count = 0
        
        for device in devices:
            # Проверяем в базе
            existing = NetworkEquipment.objects.filter(
                Q(ip_address=device['ip']) | 
                Q(mac_address=device['mac'])
            ).first()
            
            devices_with_status.append({
                **device,
                'in_database': bool(existing),
                'existing_device': {
                    'id': existing.id,
                    'name': existing.name
                } if existing else None
            })
            
            if existing:
                existing_count += 1
            else:
                new_count += 1
        
        return JsonResponse({
            'scan_info': scan_data,
            'devices': devices_with_status,
            'new_count': new_count,
            'existing_count': existing_count
        })


class AddScannedDeviceView(AdminRequiredMixin, View):
    """API для добавления устройства"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            
            # Проверяем, нет ли уже в базе
            if NetworkEquipment.objects.filter(ip_address=data['ip']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Устройство уже существует'
                })
            
            # Создаем имя устройства
            device_name = data.get('hostname') or f"Устройство {data['ip']}"
            
            # Определяем тип устройства
            device_type = self._detect_device_type(data)
            
            # Создаем устройство
            equipment = NetworkEquipment.objects.create(
                name=device_name,
                type=device_type,
                ip_address=data['ip'],
                mac_address=data['mac'] if data['mac'] != 'не определен' else None,
                manufacturer=data.get('manufacturer'),
                status='active',
                scan_source='auto'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Устройство добавлено',
                'id': equipment.id,
                'name': equipment.name
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def _detect_device_type(self, device_data):
        """Определение типа устройства по данным"""
        manufacturer = device_data.get('manufacturer', '').lower()
        
        if any(word in manufacturer for word in ['mikrotik', 'routerboard', 'cisco', 'juniper']):
            return 'router'
        elif any(word in manufacturer for word in ['ubiquiti', 'aruba', 'ruckus']):
            return 'access_point'
        elif any(word in manufacturer for word in ['hp', 'arista', 'extreme']):
            return 'switch'
        elif any(word in manufacturer for word in ['grandstream', 'yealink', 'polycom']):
            return 'voip_phone'
        elif any(word in manufacturer for word in ['hp', 'kyocera', 'xerox', 'canon']):
            return 'printer'
        elif any(word in manufacturer for word in ['dell', 'lenovo', 'supermicro']):
            return 'server'
        
        return 'unknown'


class BulkAddDevicesView(AdminRequiredMixin, View):
    """Массовое добавление устройств"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            device_ips = data.get('devices', [])
            scan_results = request.session.get('network_scan_results', {}).get('devices', [])
            
            added_devices = []
            skipped_devices = []
            
            for device_data in scan_results:
                if device_data['ip'] in device_ips:
                    # Проверяем, нет ли уже в базе
                    if NetworkEquipment.objects.filter(ip_address=device_data['ip']).exists():
                        skipped_devices.append(device_data['ip'])
                        continue
                    
                    # Создаем устройство
                    device_type = AddScannedDeviceView()._detect_device_type(device_data)
                    device_name = device_data.get('hostname') or f"Устройство {device_data['ip']}"
                    
                    equipment = NetworkEquipment.objects.create(
                        name=device_name,
                        type=device_type,
                        ip_address=device_data['ip'],
                        mac_address=device_data.get('mac'),
                        manufacturer=device_data.get('manufacturer'),
                        status='active',
                        scan_source='auto'
                    )
                    
                    added_devices.append(equipment.name)
            
            return JsonResponse({
                'success': True,
                'added': added_devices,
                'skipped': skipped_devices,
                'added_count': len(added_devices)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })