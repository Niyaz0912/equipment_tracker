# network_shell.py - скрипт для просмотра данных в таблицах network
import os
import django
import sys

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from network.models import Location, NetworkEquipment, Subnet, IPAddress

print("="*60)
print("ПРОСМОТР ДАННЫХ В ТАБЛИЦАХ NETWORK")
print("="*60)

# 1. NetworkEquipment (основная таблица)
print("\n📦 ТАБЛИЦА: NetworkEquipment")
print("-"*40)
equipments = NetworkEquipment.objects.all()
print(f"Всего записей: {equipments.count()}")

for i, eq in enumerate(equipments[:10], 1):  # Первые 10 записей
    print(f"{i}. {eq.name} (ID: {eq.id})")
    print(f"   Тип: {eq.type}, IP: {eq.ip_address}, MAC: {eq.mac_address}")
    print(f"   Производитель: {eq.manufacturer}, Модель: {eq.model}")
    print(f"   Статус: {eq.status}, Источник: {eq.scan_source}")
    print()

# 2. Location
print("\n📍 ТАБЛИЦА: Location")
print("-"*40)
locations = Location.objects.all()
print(f"Всего записей: {locations.count()}")
for loc in locations:
    print(f"{loc.id}. {loc.name} - {loc.address or 'нет адреса'}")

# 3. Subnet
print("\n🌐 ТАБЛИЦА: Subnet")
print("-"*40)
subnets = Subnet.objects.all()
print(f"Всего записей: {subnets.count()}")
for subnet in subnets:
    print(f"{subnet.id}. {subnet.network} - {subnet.description}")

# 4. IPAddress
print("\n📡 ТАБЛИЦА: IPAddress")
print("-"*40)
ips = IPAddress.objects.all()
print(f"Всего записей: {ips.count()}")
for ip in ips[:5]:  # Первые 5 записей
    device_name = ip.device.name if ip.device else "нет устройства"
    print(f"{ip.id}. {ip.address} ({ip.status}) - {device_name}")

print("\n" + "="*60)
print("ДОПОЛНИТЕЛЬНЫЕ СТАТИСТИКИ:")
print("-"*60)

# Статистика по scan_source
from django.db.models import Count
print("\n📊 Статистика по источнику обнаружения:")
source_stats = NetworkEquipment.objects.values('scan_source').annotate(
    count=Count('id')
).order_by('-count')
for stat in source_stats:
    source = stat['scan_source'] or 'не указан'
    print(f"   {source}: {stat['count']} устройств")

# Статистика по типам
print("\n📊 Статистика по типам оборудования:")
type_stats = NetworkEquipment.objects.values('type').annotate(
    count=Count('id')
).order_by('-count')
for stat in type_stats:
    print(f"   {stat['type']}: {stat['count']} устройств")

print("\n✅ Готово!")