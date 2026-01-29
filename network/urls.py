# network/urls.py
from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    # Главная страница (оборудование + сканер)
    path('', views.EquipmentListView.as_view(), name='equipment_list'),
    
    # Оборудование
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    
    # Подсети
    path('subnets/', views.SubnetListView.as_view(), name='subnet_list'),
    path('subnets/<int:pk>/', views.SubnetDetailView.as_view(), name='subnet_detail'),
    
    # Карта сети
    path('network-map/', views.NetworkMapView.as_view(), name='network_map'),
    
    # IP-менеджмент (замена поиску IP)
    path('ip-management/', views.IPManagementView.as_view(), name='ip_management'),
    
    # API для сканирования
    path('api/scan/', views.ScanDevicesAPIView.as_view(), name='api_scan'),
    path('api/scan-results/', views.GetScanResultsAPIView.as_view(), name='api_scan_results'),
    path('api/add-device/', views.AddScannedDeviceView.as_view(), name='api_add_device'),
    path('api/bulk-add/', views.BulkAddDevicesView.as_view(), name='api_bulk_add'),
]
