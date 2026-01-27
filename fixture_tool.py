#!/usr/bin/env python3
"""
Минимальная утилита для работы с фикстурами Equipment Tracker
Команды: create, load, list, cleanup
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# ========== НАСТРОЙКА DJANGO ==========
def setup_django():
    """Настройка Django - должна быть первой функцией"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    
    try:
        import django
        django.setup()
        print("✅ Django настроен")
        return True
    except Exception as e:
        print(f"❌ Ошибка Django: {e}")
        return False

# ========== ОСНОВНОЙ КЛАСС ==========
class FixtureTool:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.fixtures_dir = self.base_dir / 'fixtures'
        self.fixtures_dir.mkdir(exist_ok=True)
        
        # Порядок загрузки важен для связей!
        self.apps_order = ['employees', 'equipments', 'network']
        
    # ========== СОЗДАНИЕ ФИКСТУР ==========
    def create_all(self):
        """Создает фикстуры для всех приложений"""
        print("📦 Создаю фикстуры для всех приложений...")
        
        for app in self.apps_order:
            self._create_fixture(app)
        
        print("✅ Все фикстуры созданы")
        self.list_fixtures()
    
    def create_app(self, app_name):
        """Создает фикстуру для конкретного приложения"""
        if app_name not in self.apps_order:
            print(f"❌ Приложение '{app_name}' не найдено")
            print(f"   Доступные: {', '.join(self.apps_order)}")
            return
        
        self._create_fixture(app_name)
        print(f"✅ Фикстура для '{app_name}' создана")
    
    def _create_fixture(self, app_name):
        """Внутренний метод создания фикстуры"""
        from django.core.management import call_command
        
        filename = f"{app_name}.json"
        filepath = self.fixtures_dir / filename
        
        try:
            print(f"  Создаю {filename}...", end=' ')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                call_command('dumpdata', app_name, indent=2, stdout=f)
            
            # Проверяем размер
            size_kb = filepath.stat().st_size / 1024
            print(f"✅ ({size_kb:.1f} KB)")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # ========== ЗАГРУЗКА ФИКСТУР ==========
    def load_all(self, clear_db=False):
        """Загружает все фикстуры в правильном порядке"""
        if clear_db:
            if input("⚠️ Очистить базу данных? (yes/no): ").lower() != 'yes':
                print("❌ Отменено")
                return
            self._clear_database()
        
        print("📥 Загружаю все фикстуры...")
        
        for app in self.apps_order:
            self._load_fixture(f"{app}.json")
        
        print("✅ Все фикстуры загружены")
    
    def load_app(self, app_name, clear_db=False):
        """Загружает фикстуру конкретного приложения"""
        if clear_db:
            if input("⚠️ Очистить базу данных? (yes/no): ").lower() != 'yes':
                print("❌ Отменено")
                return
            self._clear_database()
        
        filename = f"{app_name}.json"
        self._load_fixture(filename)
    
    def _load_fixture(self, filename):
        """Внутренний метод загрузки фикстуры"""
        from django.core.management import call_command
        
        filepath = self.fixtures_dir / filename
        
        if not filepath.exists():
            print(f"❌ Файл не найден: {filename}")
            return
        
        try:
            print(f"  Загружаю {filename}...", end=' ')
            call_command('loaddata', str(filepath))
            print("✅")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def _clear_database(self):
        """Очищает базу данных"""
        from django.core.management import call_command
        call_command('flush', '--no-input')
        print("🗑️ База данных очищена")
    
    # ========== УТИЛИТЫ ==========
    def list_fixtures(self):
        """Показывает список всех фикстур"""
        print("\n📁 Список фикстур:")
        print("-" * 40)
        
        files = list(self.fixtures_dir.glob('*.json'))
        
        if not files:
            print("Файлы не найдены")
            return
        
        total_size = 0
        for i, file in enumerate(sorted(files), 1):
            size_kb = file.stat().st_size / 1024
            total_size += size_kb
            
            # Статус (есть ли данные)
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data)
            
            print(f"{i:2}. {file.name:25} {size_kb:6.1f} KB ({count} записей)")
        
        print("-" * 40)
        print(f"Всего: {len(files)} файлов, {total_size:.1f} KB")
    
    def cleanup(self, keep=5):
        """Удаляет старые фикстуры, оставляет только keep последних"""
        print(f"🧹 Очистка фикстур (оставляю {keep} последних)...")
        
        backup_files = []
        for app in self.apps_order:
            files = list(self.fixtures_dir.glob(f"{app}_*.json"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file in files[keep:]:
                print(f"  Удаляю {file.name}...", end=' ')
                file.unlink()
                print("✅")
        
        print("✅ Очистка завершена")

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    parser = argparse.ArgumentParser(
        description='Минимальная утилита для фикстур Equipment Tracker'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # create
    create_parser = subparsers.add_parser('create', help='Создать фикстуры')
    create_group = create_parser.add_mutually_exclusive_group()
    create_group.add_argument('--all', action='store_true', help='Все приложения')
    create_group.add_argument('--app', help='Конкретное приложение')
    
    # load
    load_parser = subparsers.add_parser('load', help='Загрузить фикстуры')
    load_group = load_parser.add_mutually_exclusive_group()
    load_group.add_argument('--all', action='store_true', help='Все приложения')
    load_group.add_argument('--app', help='Конкретное приложение')
    load_parser.add_argument('--clear', '-c', action='store_true', help='Очистить БД перед загрузкой')
    
    # list
    subparsers.add_parser('list', help='Показать список фикстур')
    
    # cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Очистить старые фикстуры')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Сколько оставить файлов')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Инициализация Django
    if not setup_django():
        sys.exit(1)
    
    # Запуск команды
    tool = FixtureTool()
    
    if args.command == 'create':
        if args.all:
            tool.create_all()
        elif args.app:
            tool.create_app(args.app)
        else:
            print("❌ Укажите --all или --app <имя>")
    
    elif args.command == 'load':
        if args.all:
            tool.load_all(clear_db=args.clear)
        elif args.app:
            tool.load_app(args.app, clear_db=args.clear)
        else:
            print("❌ Укажите --all или --app <имя>")
    
    elif args.command == 'list':
        tool.list_fixtures()
    
    elif args.command == 'cleanup':
        tool.cleanup(keep=args.keep)

if __name__ == '__main__':
    main()