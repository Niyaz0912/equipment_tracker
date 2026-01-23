from django.urls import path
from . import views

app_name = 'network'

urlpatterns = [
    path('', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    
]