from django.urls import path
from . import views

app_name = 'printer_monitor'

urlpatterns = [
    path('', views.PrinterStatusView.as_view(), name='printer_monitor'),
    
    # API для AJAX
    path('api/check-printer/<str:ip>/', views.api_check_printer, name='api_check_printer'),
    path('api/check-all-printers/', views.api_check_all_printers, name='api_check_all_printers'),
    path('', views.PrinterStatusView.as_view(), name='printer_monitor'),
]