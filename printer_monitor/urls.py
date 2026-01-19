from django.urls import path
from . import views

app_name = 'printer_monitor'

urlpatterns = [
    path('', views.PrinterStatusView.as_view(), name='status'),
    path('check/', views.CheckPrintersView.as_view(), name='check_printers'),
    path('stats/', views.PrinterStatsView.as_view(), name='stats'),
    path('problems/', views.ProblemPrintersView.as_view(), name='problems'),
]