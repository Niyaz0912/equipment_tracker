import json
from django.shortcuts import render
from django.db.models import Q
from django.views.generic import ListView, DetailView, TemplateView
from .models import Location, NetworkEquipment, Location, Subnet, IPAddress
from django.db.models import Count
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

class AdminRequiredMixin(LoginRequiredMixin):
    """Миксин для страниц, требующих админ-прав"""
    login_url = '/admin/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Сохраняем куда хотел попасть пользователь
            next_url = request.get_full_path()
            return redirect(f'/admin/login/?next={next_url}')
        return super().dispatch(request, *args, **kwargs)


class EquipmentListView(AdminRequiredMixin, ListView):
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

# views.py - обновленный NetworkMapView
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


class NetworkDashboardView(AdminRequiredMixin, TemplateView):
    """Дашборд сетевой статистики"""
    template_name = 'network/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика оборудования
        equipment = NetworkEquipment.objects.all()
        context['equipment_count'] = equipment.count()
        context['equipment'] = equipment.order_by('-created_at')[:10]  # Последние 10
        
        # Статистика локаций
        context['location_count'] = Location.objects.count()
        
        # Статистика подсетей
        context['subnet_count'] = Subnet.objects.count()
        
        # Статистика IP-адресов
        context['ip_count'] = IPAddress.objects.count()
        
        # Дополнительная статистика
        context['active_count'] = NetworkEquipment.objects.filter(status='active').count()
        context['repair_count'] = NetworkEquipment.objects.filter(status='repair').count()
        
        return context