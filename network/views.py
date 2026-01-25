from django.shortcuts import render
from django.db.models import Q
from django.views.generic import ListView, DetailView, TemplateView
from .models import Location, NetworkEquipment, Subnet, IPAddress

class EquipmentListView(ListView):
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
        
        # Передаем параметры фильтров
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


class EquipmentDetailView(DetailView):
    model = NetworkEquipment
    template_name = 'network/equipment_detail.html'
    context_object_name = 'equipment'

class IPLookupView(TemplateView):
    """Поиск: Кто на этом IP?"""
    template_name = 'network/ip_lookup.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ip = self.request.GET.get('ip', '')
        result = None
        
        if ip:
            result = IPAddress.objects.filter(address=ip).select_related('device', 'subnet').first()
        
        context['ip'] = ip
        context['result'] = result
        return context

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
        context['ip_addresses'] = IPAddress.objects.filter(
            subnet=self.object
        ).select_related('device')
        return context

class NetworkMapView(TemplateView):
    """Топология сети - визуальная схема"""
    template_name = 'network/network_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем параметры фильтрации из GET-запроса
        location_filter = self.request.GET.get('location')
        type_filter = self.request.GET.get('type')
        status_filter = self.request.GET.get('status')
        
        # Базовый запрос оборудования
        devices = NetworkEquipment.objects.all().select_related('location')
        
        # Применяем фильтры
        if location_filter:
            devices = devices.filter(location_id=location_filter)
        
        if type_filter:
            devices = devices.filter(type=type_filter)
        
        if status_filter:
            devices = devices.filter(status=status_filter)
        
        # Группируем оборудование по локациям для топологии
        locations_data = {}
        
        for device in devices:
            location_id = device.location_id if device.location else 0
            location_name = device.location.name if device.location else "Без локации"
            
            if location_id not in locations_data:
                locations_data[location_id] = {
                    'id': location_id,
                    'name': location_name,
                    'devices': [],
                    'device_stats': {
                        'router': 0, 'switch': 0, 'server': 0, 
                        'firewall': 0, 'access_point': 0, 'other': 0
                    }
                }
            
            locations_data[location_id]['devices'].append(device)
            
            # Считаем типы оборудования
            device_type = device.type if device.type else 'other'
            if device_type in locations_data[location_id]['device_stats']:
                locations_data[location_id]['device_stats'][device_type] += 1
            else:
                locations_data[location_id]['device_stats']['other'] += 1
        
        # Преобразуем в список
        network_topology = list(locations_data.values())
        
        # Считаем общее количество устройств в топологии
        filtered_devices_count = sum(len(location['devices']) for location in network_topology)
        
        # Получаем все локации для фильтра
        all_locations = Location.objects.all()
        
        # Статистика
        context.update({
            'network_topology': network_topology,
            'all_locations': all_locations,
            'total_devices': devices.count(),
            'filtered_devices_count': filtered_devices_count,  # Добавляем
            'total_locations': len(network_topology),
            'location_filter': location_filter,
            'type_filter': type_filter,
            'status_filter': status_filter,
        })
        
        return context