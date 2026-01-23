import sqlite3

def check_database():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("=" * 50)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # 1. Все таблицы
    print("\n1. ВСЕ ТАБЛИЦЫ В БАЗЕ:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        print(f"   - {table[0]}")
    
    # 2. Миграции network
    print("\n2. МИГРАЦИИ NETWORK В DJANGO_MIGRATIONS:")
    cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app='network'")
    migrations = cursor.fetchall()
    if migrations:
        for mig in migrations:
            print(f"   - {mig[0]}.{mig[1]} (применена: {mig[2]})")
    else:
        print("   - Нет записей о миграциях network")
    
    # 3. Проверка таблицы network_networkitem
    print("\n3. ПРОВЕРКА ТАБЛИЦЫ network_networkitem:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='network_networkitem'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print(f"   ✓ Таблица '{table_exists[0]}' СУЩЕСТВУЕТ")
        # Покажем структуру
        cursor.execute("PRAGMA table_info(network_networkitem)")
        columns = cursor.fetchall()
        print("   Структура таблицы:")
        for col in columns:
            print(f"     * {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    else:
        print("   ✗ Таблица 'network_networkitem' НЕ СУЩЕСТВУЕТ")
    
    conn.close()
    print("\n" + "=" * 50)

if __name__ == "__main__":
    check_database()