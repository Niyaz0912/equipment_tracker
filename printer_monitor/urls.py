# printer_monitor/urls.py
from django.urls import path
from . import views

app_name = 'printer_monitor'

urlpatterns = [
    path('', views.PrinterDashboardView.as_view(), name='dashboard'),
    path('problems/', views.ProblemPrintersView.as_view(), name='problems'),
    path('printer/<int:pk>/', views.PrinterDetailView.as_view(), name='printer_detail'),
    path('check-all/', views.check_all_printers_view, name='check_all'),
    path('check/<int:pk>/', views.CheckSinglePrinterView.as_view(), name='check_single'),
]