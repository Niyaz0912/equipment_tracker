# test_read.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import json
import os

print("=" * 50)
print("ПРОВЕРКА ФАЙЛОВ В ПРОЕКТЕ")
print("=" * 50)

# Какие файлы есть
files_to_check = ['identified_devices.json', 'active_hosts.txt', 'network_scan_debug.json']
for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file} - НАЙДЕН")
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   Размер: {len(content)} символов")
                print(f"   Первые 200 символов:")
                print(f"   {content[:200]}...")
        except:
            print(f"   Не удалось прочитать")
    else:
        print(f"❌ {file} - НЕ НАЙДЕН")

print("\n" + "=" * 50)
print("ЧТЕНИЕ identified_devices.json (если есть)")
print("=" * 50)

if os.path.exists('identified_devices.json'):
    try:
        with open('identified_devices.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Тип данных: {type(data)}")
        
        if isinstance(data, list):
            print(f"Количество элементов в списке: {len(data)}")
            if data:
                print("\nПЕРВЫЕ 3 УСТРОЙСТВА:")
                for i, device in enumerate(data[:3]):
                    print(f"\nУстройство {i+1}:")
                    if isinstance(device, dict):
                        for key, value in device.items():
                            print(f"  {key}: {value}")
                    else:
                        print(f"  {device}")
                        
        elif isinstance(data, dict):
            print("Ключи в словаре:", list(data.keys()))
            if 'devices' in data and isinstance(data['devices'], list):
                print(f"Количество устройств: {len(data['devices'])}")
                if data['devices']:
                    print("\nПЕРВЫЕ 3 УСТРОЙСТВА:")
                    for i, device in enumerate(data['devices'][:3]):
                        print(f"\nУстройство {i+1}:")
                        for key, value in device.items():
                            print(f"  {key}: {value}")
                            
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
else:
    print("Файл не найден")

print("\n" + "=" * 50)
print("ЧТЕНИЕ active_hosts.txt (если есть)")
print("=" * 50)

if os.path.exists('active_hosts.txt'):
    try:
        with open('active_hosts.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Количество строк: {len(lines)}")
        print("\nПЕРВЫЕ 10 СТРОК:")
        for i, line in enumerate(lines[:10]):
            print(f"{i+1}: {line.strip()}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
else:
    print("Файл не найден")

input("\nНажми Enter для выхода...")