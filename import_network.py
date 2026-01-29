# import_network.py
import os
import django
import sys

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ТЕПЕРЬ импортируем модели
from network.models import NetworkEquipment, Location
from django.core import serializers

def import_from_scan():
    """Импортирует найденные устройства"""
    
    print("📥 Импорт данных из сканирования...")
    
    # 1. Прочитай найденные IP
    try:
        with open('active_hosts.txt', 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Файл active_hosts.txt не найден")
        return
    
    print(f"📋 Найдено IP: {len(ips)}")
    
    # 2. Создай локации
    locations_map = {}
    
    # Все локации из твоих подсетей
    location_data = [
        ('192.168.8', "Network device & server", "Основное сетевое оборудование"),
        ('192.168.9', "Kavleger", "Сеть Kavleger"),
        ('192.168.10', "Corp network", "Корпоративная сеть"),
        ('192.168.11', "Corp network 2", "Продолжение корпоративной сети"),
        ('192.168.12', "DJns crankos", "Сеть DJns crankos"),
    ]
    
    for prefix, name, desc in location_data:
        loc, created = Location.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        locations_map[prefix] = loc
    
    # 3. Импортируй устройства (первые 100 для теста)
    imported = 0
    skipped = 0
    
    for ip in ips[:100]:  # Первые 100 для теста
        network_part = '.'.join(ip.split('.')[:3])
        location = locations_map.get(network_part)
        
        if not location:
            skipped += 1
            continue
        
        # Определи тип по IP
        device_type = 'other'
        if ip.endswith('.1'):  # Шлюзы
            device_type = 'router'
        elif ip.startswith('192.168.8.6'):  # Серверы
            device_type = 'server'
        
        # Проверь, не существует ли уже
        if not NetworkEquipment.objects.filter(ip_address=ip).exists():
            NetworkEquipment.objects.create(
                name=f"Устройство {ip}",
                type=device_type,
                ip_address=ip,
                location=location,
                status='active',
                notes='Найдено автоматическим сканированием'
            )
            imported += 1
    
    print(f"✅ Импортировано: {imported} устройств")
    print(f"⏭️  Пропущено: {skipped} (неизвестная подсеть)")
    
    # 4. Покажи статистику
    print(f"\n📊 В базе сейчас: {NetworkEquipment.objects.count()} устройств")
    
    # Создай фикстуру
    create_fixture()

def create_fixture():
    """Создаёт фикстуру со всеми данными network"""
    from django.core import serializers
    
    print("\n💾 Создание фикстуры...")
    
    # Получи все объекты
    all_objects = []
    
    # Location
    locations = Location.objects.all()
    all_objects.extend(locations)
    
    # NetworkEquipment
    equipment = NetworkEquipment.objects.all()
    all_objects.extend(equipment)
    
    # Сохрани
    with open('fixtures/network_real_data.json', 'w', encoding='utf-8') as f:
        serializers.serialize('json', all_objects, stream=f, indent=2, use_natural_foreign_keys=True)
    
    print(f"✅ Фикстура создана: fixtures/network_real_data.json")
    print(f"   Всего записей: {len(all_objects)}")

if __name__ == "__main__":
    import_from_scan()