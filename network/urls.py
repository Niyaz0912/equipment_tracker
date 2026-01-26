from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    path('', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    path('ip-lookup/', views.IPLookupView.as_view(), name='ip_lookup'),
    path('subnets/', views.SubnetListView.as_view(), name='subnet_list'),
    path('subnets/<int:pk>/', views.SubnetDetailView.as_view(), name='subnet_detail'),
    path('network-map/', views.NetworkMapView.as_view(), name='network_map'),       # Векторная схема
    path('dashboard/', views.NetworkDashboardView.as_view(), name='dashboard'),     # Дашборд (ДРУГОЙ класс!)
]