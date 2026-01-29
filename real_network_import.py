# real_network_import.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from network.models import NetworkEquipment, Location

# Очисти старое
NetworkEquipment.objects.all().delete()
print("✅ Старые данные удалены")

# Создай локации
locations = {
    'network': Location.objects.get_or_create(name="Сетевая инфраструктура")[0],
    'servers': Location.objects.get_or_create(name="Серверная")[0],
    'kavleger': Location.objects.get_or_create(name="Kavleger")[0],
    'corp': Location.objects.get_or_create(name="Офис")[0],
}

# ТОЛЬКО устройства, о которых есть информация
real_devices = [
    # СЕТЕВОЕ ОБОРУДОВАНИЕ (шлюзы - TTL=64)
    {
        'name': 'Основной маршрутизатор',
        'type': 'router',
        'model': 'Неизвестно (TTL=64)',
        'ip': '192.168.8.1',
        'location': locations['network'],
        'notes': 'Шлюз сети 192.168.8.0/27. TTL=64, требуется уточнение модели'
    },
    {
        'name': 'Маршрутизатор Kavleger',
        'type': 'router',
        'model': 'Неизвестно (TTL=64)',
        'ip': '192.168.9.1',
        'location': locations['kavleger'],
        'notes': 'Шлюз сети 192.168.9.0/24. TTL=64'
    },
    
    # СЕРВЕРЫ (из подсети 192.168.8.64/26)
    {
        'name': 'Сервер 1',
        'type': 'server',
        'model': 'Неизвестно',
        'ip': '192.168.8.65',
        'location': locations['servers'],
        'notes': 'Серверная стойка'
    },
    {
        'name': 'Сервер 2',
        'type': 'server',
        'model': 'Неизвестно',
        'ip': '192.168.8.66',
        'location': locations['servers'],
        'notes': 'Серверная стойка'
    },
    
    # КОМПЬЮТЕРЫ (примеры, если знаешь)
    # {
    #     'name': 'Рабочая станция бухгалтерии',
    #     'type': 'other',
    #     'model': 'HP EliteDesk',
    #     'ip': '192.168.10.104',
    #     'location': locations['corp'],
    #     'notes': 'Сотрудник: Иванов И.И.'
    # },
]

# Добавь только эти устройства
for dev in real_devices:
    NetworkEquipment.objects.create(
        name=dev['name'],
        type=dev['type'],
        model=dev['model'],
        ip_address=dev['ip'],
        location=dev['location'],
        notes=dev['notes'],
        status='active'
    )

print(f"✅ Добавлено {len(real_devices)} РЕАЛЬНЫХ устройств")
print("\n📋 Список добавленного:")
for dev in NetworkEquipment.objects.all():
    print(f"  • {dev.name} ({dev.ip_address}) - {dev.get_type_display()}")