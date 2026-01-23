from django import forms
from .models import NetworkEquipment, Location

class NetworkEquipmentForm(forms.ModelForm):
    class Meta:
        model = NetworkEquipment
        fields = [
            'name', 'type', 'model', 'serial_number',  # <-- type вместо equipment_type
            'inventory_number', 'location', 'rack', 'unit', 
            'ip_address', 'mac_address', 'status', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Core Switch 1'}),
            'equipment_type': forms.Select(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'rack': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Номер стойки'}),
            'unit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Номер юнита'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.1'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00:1A:2B:3C:4D:5E'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Название',
            'equipment_type': 'Тип оборудования',
            'model': 'Модель',
            'serial_number': 'Серийный номер',
            'inventory_number': 'Инвентарный номер',
            'location': 'Местонахождение',
            'rack': 'Стойка',
            'unit': 'Юнит',
            'ip_address': 'IP-адрес',
            'mac_address': 'MAC-адрес',
            'status': 'Статус',
            'notes': 'Примечания',
        }