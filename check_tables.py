import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")

# 1. Все таблицы
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = cursor.fetchall()
    
    print("Все таблицы в базе:")
    for table in all_tables:
        print(f"  {table[0]}")

# 2. Таблицы network
print("\n=== ТАБЛИЦЫ NETWORK ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'network_%'")
    network_tables = cursor.fetchall()
    
    if network_tables:
        print("Таблицы network найдены:")
        for table in network_tables:
            print(f"  ✓ {table[0]}")
    else:
        print("❌ Таблицы network НЕ найдены!")

# 3. Миграции network
print("\n=== МИГРАЦИИ NETWORK ===")
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app = 'network'")
    migrations = cursor.fetchall()
    
    if migrations:
        print("Записи о миграциях network:")
        for mig in migrations:
            status = "✓ применена" if mig[2] else "✗ не применена"
            print(f"  {mig[0]}.{mig[1]} - {status}")
    else:
        print("❌ Нет записей о миграциях network")