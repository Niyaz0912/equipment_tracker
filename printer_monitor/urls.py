from django.urls import path
from . import views

urlpatterns = [
    path('', views.PrinterStatusView.as_view(), name='printer_status'),
    path('check/', views.check_printers_now, name='check_printers'),
]