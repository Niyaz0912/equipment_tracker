from django.shortcuts import render
from django.db.models import Q
from django.views.generic import ListView, DetailView
from .models import Location, NetworkEquipment

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