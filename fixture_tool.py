import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"Ошибка инициализации Django: {e}")
    print("Запускаем в режиме без Django...")

# Константы
BASE_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = BASE_DIR / 'fixtures'
DEFAULT_APPS = ['employees', 'equipments']
BACKUP_DIR = BASE_DIR / 'backups'


class FixtureTool:
    """Утилита для работы с фикстурами"""
    
    def __init__(self):
        self.ensure_directories()
    
    def ensure_directories(self):
        """Создает необходимые директории"""
        for directory in [FIXTURES_DIR, BACKUP_DIR]:
            directory.mkdir(exist_ok=True)
    
    def create_fixtures(self, apps=None, output_name=None, indent=2):
        """
        Создает фикстуры для указанных приложений
        
        Args:
            apps: список приложений или 'all' для всех
            output_name: имя выходного файла (без .json)
            indent: отступ в JSON
        """
        if apps is None:
            apps = DEFAULT_APPS
        elif apps == 'all':
            # Получаем все приложения кроме стандартных Django
            from django.apps import apps as django_apps
            apps = [
                app.name.split('.')[-1] 
                for app in django_apps.get_app_configs()
                if not app.name.startswith(('django.', 'auth.', 'admin.', 'sessions', 'contenttypes'))
            ]
        
        print(f"Создаю фикстуры для приложений: {', '.join(apps)}")
        
        for app in apps:
            try:
                # Имя файла
                if output_name:
                    filename = f"{output_name}_{app}.json"
                else:
                    filename = f"{app}.json"
                
                filepath = FIXTURES_DIR / filename
                
                # Команда dumpdata
                cmd = [
                    sys.executable, 'manage.py', 'dumpdata',
                    app,
                    '--indent', str(indent),
                    '--output', str(filepath)
                ]
                
                print(f"  Создаю {filename}...", end=' ')
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Проверяем и исправляем кодировку если нужно
                    self.ensure_utf8(filepath)
                    print("✅ Успешно")
                else:
                    print(f"❌ Ошибка: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Ошибка при создании фикстур для {app}: {e}")
        
        print("\nФикстуры созданы в папке:", FIXTURES_DIR)
    
    def load_fixtures(self, fixtures=None, clear_db=False):
        """
        Загружает фикстуры в базу данных
        
        Args:
            fixtures: список файлов фикстур или 'all' для всех
            clear_db: очистить базу перед загрузкой
        """
        if clear_db:
            confirm = input("Вы уверены, что хотите очистить базу данных? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Отменено")
                return
            
            print("Очищаю базу данных...")
            subprocess.run([sys.executable, 'manage.py', 'flush', '--no-input'])
        
        if fixtures is None or fixtures == 'all':
            # Загружаем все JSON файлы из fixtures
            fixtures = list(FIXTURES_DIR.glob('*.json'))
        elif isinstance(fixtures, str):
            fixtures = [FIXTURES_DIR / fixtures]
        
        print(f"Загружаю {len(fixtures)} фикстур...")
        
        for fixture in fixtures:
            if not fixture.exists():
                print(f"❌ Файл не найден: {fixture}")
                continue
            
            print(f"  Загружаю {fixture.name}...", end=' ')
            
            cmd = [sys.executable, 'manage.py', 'loaddata', str(fixture)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Успешно")
            else:
                print(f"❌ Ошибка: {result.stderr}")
    
    def backup_database(self, backup_name=None):
        """Создает резервную копию всей базы данных"""
        import datetime
        
        if backup_name is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
        
        backup_file = BACKUP_DIR / f"{backup_name}.json"
        
        print(f"Создаю резервную копию в {backup_file}...")
        
        cmd = [
            sys.executable, 'manage.py', 'dumpdata',
            '--all',
            '--indent', '2',
            '--output', str(backup_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            self.ensure_utf8(backup_file)
            print(f"✅ Резервная копия создана: {backup_file}")
            
            # Создаем список файлов
            files_list = BACKUP_DIR / 'backup_files.txt'
            with open(files_list, 'a', encoding='utf-8') as f:
                f.write(f"{backup_name}.json\n")
            
            return backup_file
        else:
            print(f"❌ Ошибка: {result.stderr}")
            return None
    
    def ensure_utf8(self, filepath):
        """Гарантирует, что файл в кодировке UTF-8"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Перезаписываем с явным указанием UTF-8
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True
        except UnicodeDecodeError:
            # Файл не в UTF-8, конвертируем
            try:
                with open(filepath, 'r', encoding='cp1251') as f:
                    content = f.read()
                
                with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                print(f"  Конвертирован в UTF-8: {filepath.name}")
                return True
            except Exception as e:
                print(f"  Ошибка конвертации {filepath.name}: {e}")
                return False
    
    def list_fixtures(self):
        """Показывает список доступных фикстур"""
        print("Доступные фикстуры:")
        print("-" * 40)
        
        fixtures = list(FIXTURES_DIR.glob('*.json'))
        
        if not fixtures:
            print("Файлы фикстур не найдены")
            return
        
        for i, fixture in enumerate(fixtures, 1):
            size = fixture.stat().st_size / 1024  # Размер в KB
            print(f"{i:2}. {fixture.name:30} {size:6.1f} KB")
    
    def setup_new_deployment(self):
        """Настройка нового развертывания"""
        print("Настройка нового развертывания...")
        print("-" * 40)
        
        # 1. Создаем миграции
        print("1. Создаю миграции...")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'])
        
        # 2. Применяем миграции
        print("2. Применяю миграции...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'])
        
        # 3. Загружаем фикстуры
        print("3. Загружаю фикстуры...")
        self.load_fixtures('all')
        
        # 4. Создаем суперпользователя если его нет
        print("4. Проверяю суперпользователя...")
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(is_superuser=True).exists():
                print("   Создайте суперпользователя:")
                subprocess.run([sys.executable, 'manage.py', 'createsuperuser'])
            else:
                print("   Суперпользователь уже существует")
        except:
            print("   Не удалось проверить суперпользователя")
        
        print("\n✅ Настройка завершена!")
        print("Запустите сервер: python manage.py runserver")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(
        description='Утилита для работы с фикстурами Equipment Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s create                    # Создать фикстуры по умолчанию
  %(prog)s create --all              # Создать фикстуры для всех приложений
  %(prog)s create -a employees       # Только сотрудники
  %(prog)s load                      # Загрузить все фикстуры
  %(prog)s load --file employees.json # Загрузить конкретную фикстуру
  %(prog)s backup                    # Создать резервную копию
  %(prog)s setup                     # Настройка нового развертывания
  %(prog)s list                      # Показать список фикстур
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда create
    create_parser = subparsers.add_parser('create', help='Создать фикстуры')
    create_parser.add_argument('apps', nargs='*', default=['employees', 'equipments'],
                              help='Приложения для дампа (по умолчанию: employees equipments)')
    create_parser.add_argument('--all', action='store_true', 
                              help='Создать фикстуры для всех приложений')
    create_parser.add_argument('--output', '-o', 
                              help='Имя выходного файла (без .json)')
    create_parser.add_argument('--indent', '-i', type=int, default=2,
                              help='Отступ в JSON (по умолчанию: 2)')
    
    # Команда load
    load_parser = subparsers.add_parser('load', help='Загрузить фикстуры')
    load_parser.add_argument('files', nargs='*', 
                            help='Файлы для загрузки (по умолчанию: все)')
    load_parser.add_argument('--clear', '-c', action='store_true',
                            help='Очистить базу данных перед загрузкой')
    
    # Команда backup
    backup_parser = subparsers.add_parser('backup', help='Создать резервную копию')
    backup_parser.add_argument('--name', '-n', 
                              help='Имя резервной копии')
    
    # Команда setup
    subparsers.add_parser('setup', help='Настройка нового развертывания')
    
    # Команда list
    subparsers.add_parser('list', help='Показать список фикстур')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tool = FixtureTool()
    
    if args.command == 'create':
        if args.all:
            tool.create_fixtures(apps='all', output_name=args.output, indent=args.indent)
        else:
            tool.create_fixtures(apps=args.apps, output_name=args.output, indent=args.indent)
    
    elif args.command == 'load':
        if args.files:
            tool.load_fixtures(fixtures=args.files, clear_db=args.clear)
        else:
            tool.load_fixtures(fixtures='all', clear_db=args.clear)
    
    elif args.command == 'backup':
        tool.backup_database(args.name)
    
    elif args.command == 'setup':
        tool.setup_new_deployment()
    
    elif args.command == 'list':
        tool.list_fixtures()


if __name__ == '__main__':
    main()
    