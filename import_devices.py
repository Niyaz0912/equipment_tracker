# import_devices.py
import json
from network.models import NetworkEquipment, Location

def import_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        devices = json.load(f)
    
    # Создаем общую локацию для начала
    default_location, _ = Location.objects.get_or_create(
        name="Основная сеть",
        defaults={'description': 'Автоматически импортированные устройства'}
    )
    
    for device in devices:
        NetworkEquipment.objects.get_or_create(
            ip_address=device['ip'],
            defaults={
                'name': device['hostname'] or device['ip'],
                'type': 'other',  # Нужно будет уточнить по device_type
                'model': 'Не определена',
                'location': default_location,
                'status': 'active',
                'notes': f"Обнаружено автоматически. Порты: {device.get('ports', [])}"
            }
        )
    
    print(f"Импортировано {len(devices)} устройств")