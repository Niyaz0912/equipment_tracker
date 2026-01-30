# network/urls.py
from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    # Главная страница (ОБОРУДОВАНИЕ)
    path('', views.EquipmentListView.as_view(), name='equipment_list'),
    
    # Оборудование
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    
    # Подсети
    path('subnets/', views.SubnetListView.as_view(), name='subnet_list'),
    path('subnets/<int:pk>/', views.SubnetDetailView.as_view(), name='subnet_detail'),
    
    # Карта сети
    path('network-map/', views.NetworkMapView.as_view(), name='network_map'),
    
    # IP-менеджмент
    path('ip-management/', views.IPManagementView.as_view(), name='ip_management'),
    
    # ============ СКАНЕР СЕТИ (ПРОСТОЙ ВАРИАНТ) ============
    # Страница сканера
    path('scanner/', views.NetworkScannerView.as_view(), name='scanner'),
    
    # Запуск сканирования и показ результатов
    path('scan-results/', views.ScanResultsView.as_view(), name='scan_results'),
    
    # Добавление одного устройства
    path('add-device/', views.AddDeviceView.as_view(), name='add_device'),
    
    # Массовое добавление устройств
    path('bulk-add-devices/', views.BulkAddDevicesView.as_view(), name='bulk_add_devices'),
]
