from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Location, NetworkEquipment
from .forms import NetworkEquipmentForm

class EquipmentListView(ListView):
    model = NetworkEquipment
    template_name = 'network/equipment_list.html'
    context_object_name = 'equipments'
    
    def get_queryset(self):
        queryset = NetworkEquipment.objects.all()
        
        # Используем only() для загрузки только существующих полей
        queryset = queryset.only(
            'id', 'name', 'type', 'model', 'ip_address', 
            'status', 'location_id'
        )
        
        # Фильтрация по статусу
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(model__icontains=search_query)
                # Убираем serial_number и inventory_number, так как их пока нет в базе
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика (только с существующими полями)
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
    
    def get_queryset(self):
        # Только существующие поля
        return NetworkEquipment.objects.only(
            'id', 'name', 'type', 'model', 'ip_address', 
            'status', 'description', 'location_id'
        )


class EquipmentCreateView(CreateView):
    model = NetworkEquipment
    form_class = NetworkEquipmentForm
    template_name = 'network/equipment_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить сетевое оборудование'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Оборудование "{self.object.name}" успешно добавлено!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('network:equipment_detail', kwargs={'pk': self.object.pk})


class EquipmentUpdateView(UpdateView):
    model = NetworkEquipment
    form_class = NetworkEquipmentForm
    template_name = 'network/equipment_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактировать: {self.object.name}'
        context['equipment'] = self.object
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Оборудование "{self.object.name}" успешно обновлено!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('network:equipment_detail', kwargs={'pk': self.object.pk})


class EquipmentDeleteView(DeleteView):
    model = NetworkEquipment
    template_name = 'network/equipment_confirm_delete.html'
    context_object_name = 'equipment'
    success_url = reverse_lazy('network:equipment_list')
    
    def form_valid(self, form):
        equipment_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f'Оборудование "{equipment_name}" удалено!')
        return response