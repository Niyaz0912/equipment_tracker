# network/views.py
from django.shortcuts import render
from .models import NetworkEquipment, Location

def dashboard(request):
    equipment = NetworkEquipment.objects.all()
    locations = Location.objects.all()
    
    return render(request, 'network/dashboard.html', {
        'equipment': equipment,
        'equipment_count': equipment.count(),
        'locations': locations,
        'location_count': locations.count(),
    })