# excel_export/urls.py
from django.urls import path
from . import views

app_name = 'excel_export'

urlpatterns = [
    path('export/', views.export_excel, name='export_excel'),
]