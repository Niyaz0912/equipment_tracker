# employees/urls.py
from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('export-excel/', views.export_employees_excel, name='export_excel'),
]