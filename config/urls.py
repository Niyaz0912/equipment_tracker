# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('equipment/', include('equipments.urls')),
    path('employees/', include('employees.urls')),
    path('', RedirectView.as_view(url='/equipment/', permanent=False)),
    path('export/', include('excel_export.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
