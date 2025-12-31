# equipments/urls.py
from django.urls import path
from . import views

app_name = 'equipments'

urlpatterns = [
    path('', views.equipment_list, name='equipment_list'),
    path('search/', views.equipment_search, name='equipment_search'),
    path('<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('import/', views.equipment_import, name='equipment_import'),
    path('export-template/', views.export_template, name='export_template'),
    path('export-excel/', views.export_equipment_excel, name='export_excel'),
]