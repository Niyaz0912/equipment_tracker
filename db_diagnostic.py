# check_db.py
"""
Универсальный скрипт для проверки состояния базы данных Django проекта.
Показывает таблицы, миграции и структуру приложений.
"""

import sqlite3
import os
from datetime import datetime

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def check_database():
    """Основная функция проверки базы данных"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("ОШИБКА: База данных db.sqlite3 не найдена!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print_header(f"ПРОВЕРКА БАЗЫ ДАННЫХ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        
        # 1. Информация о базе данных
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchone()
        print(f"Файл БД: {db_info[2] if db_info else 'Неизвестно'}")
        print(f"Размер файла: {os.path.getsize(db_path) / 1024:.1f} КБ")
        
        # 2. Все таблицы
        print_header("ВСЕ ТАБЛИЦЫ В БАЗЕ")
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"Всего таблиц: {len(tables)}\n")
        
        app_tables = {}
        for table_name, table_sql in tables:
            # Определяем приложение по имени таблицы
            if '_' in table_name:
                app_name = table_name.split('_')[0]
            else:
                app_name = 'other'
            
            if app_name not in app_tables:
                app_tables[app_name] = []
            app_tables[app_name].append(table_name)
            
            # Подсчет записей в таблице
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                count = cursor.fetchone()[0]
                print(f"  {table_name:30} | Записей: {count:5}")
            except:
                print(f"  {table_name:30} | [ОШИБКА при подсчете]")
        
        # 3. Группировка по приложениям
        print_header("ТАБЛИЦЫ ПО ПРИЛОЖЕНИЯМ")
        for app_name in sorted(app_tables.keys()):
            print(f"\n{app_name.upper()}:")
            for table in sorted(app_tables[app_name]):
                print(f"  - {table}")
        
        # 4. Миграции
        print_header("МИГРАЦИИ")
        if 'django_migrations' in [t[0] for t in tables]:
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                ORDER BY applied DESC
            """)
            migrations = cursor.fetchall()
            
            # Группируем по приложениям
            migrations_by_app = {}
            for app, name, applied in migrations:
                if app not in migrations_by_app:
                    migrations_by_app[app] = []
                migrations_by_app[app].append((name, applied))
            
            for app in sorted(migrations_by_app.keys()):
                print(f"\n{app.upper()}:")
                for mig_name, mig_applied in migrations_by_app[app][:5]:  # Показываем последние 5
                    date_str = datetime.strptime(mig_applied, '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y')
                    print(f"  ✓ {mig_name} ({date_str})")
                
                if len(migrations_by_app[app]) > 5:
                    print(f"  ... и еще {len(migrations_by_app[app]) - 5} миграций")
        else:
            print("Таблица django_migrations не найдена!")
        
        # 5. Проверка конкретных таблиц (можно настраивать)
        print_header("ПРОВЕРКА КОНКРЕТНЫХ ТАБЛИЦ")
        
        tables_to_check = [
            'network_subnet',
            'network_ipaddress',
            'network_networkequipment',
            'network_location'
        ]
        
        for table_name in tables_to_check:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            exists = cursor.fetchone()
            
            if exists:
                # Количество записей
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                count = cursor.fetchone()[0]
                
                # Структура
                cursor.execute(f"PRAGMA table_info([{table_name}])")
                columns = cursor.fetchall()
                
                print(f"\n{table_name}:")
                print(f"  ✓ Существует | Записей: {count}")
                if count > 0 and columns:
                    print(f"  Столбцы ({len(columns)}):")
                    for col in columns[:3]:  # Показываем первые 3 столбца
                        print(f"    - {col[1]}: {col[2]}")
                    if len(columns) > 3:
                        print(f"    ... и еще {len(columns) - 3} столбцов")
            else:
                print(f"\n{table_name}: ✗ Не существует")
        
        conn.close()
        
        print_header("РЕКОМЕНДАЦИИ")
        if 'network_subnet' not in [t[0] for t in tables]:
            print("1. Таблица network_subnet отсутствует - нужно применить миграции")
        elif len(migrations_by_app.get('network', [])) == 0:
            print("1. У приложения 'network' нет примененных миграций")
        
        print("\nДля применения миграций выполните:")
        print("  python manage.py migrate")
        
    except Exception as e:
        print(f"ОШИБКА при проверке базы данных: {e}")

if __name__ == "__main__":
    check_database()