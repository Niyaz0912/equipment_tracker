#!/usr/bin/env python3
"""
tree.py - Утилита для отображения структуры проекта

Использование:
  python tree.py                     # показать полное дерево
  python tree.py -d 2                # глубина 2 уровня
  python tree.py --depth 3           # глубина 3 уровня
  python tree.py -a                  # показать все файлы (включая неважные)
  python tree.py --all
  python tree.py -p ./equipments     # начать с указанной папки
  python tree.py --path ./employees

Примеры:
  python tree.py -d 2 -a             # глубина 2, все файлы
  python tree.py -d 3 --path .       # глубина 3, с текущей папки
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Set, Optional

try:
    from rich.tree import Tree
    from rich import print
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Список папок и файлов для исключения
EXCLUDE_DIRS: Set[str] = {
    '__pycache__', '.git', '.venv', 'venv', 
    '.idea', '.mypy_cache', '.pytest_cache',
    'node_modules', '.npm', '.cache', 'build', 'dist'
}

EXCLUDE_FILES: Set[str] = {'.DS_Store', 'Thumbs.db'}

# Расширения важных файлов
IMPORTANT_EXTENSIONS: Set[str] = {
    '.py', '.txt', '.md', '.ini', '.cfg', 
    '.json', '.yml', '.yaml', '.html', '.css', 
    '.js', '.sql', '.sh', '.bat', '.xml'
}

# Важные файлы (без расширений)
IMPORTANT_FILES: Set[str] = {
    'manage.py', 'requirements.txt', 'README.md', 
    'Dockerfile', '.gitignore', '.env.example',
    'docker-compose.yml', 'Makefile', 'Procfile'
}


def is_important_file(filename: str, show_all: bool = False) -> bool:
    """Проверяет, является ли файл важным для отображения."""
    if show_all:
        return True  # В режиме --all показываем все
    
    if filename in IMPORTANT_FILES:
        return True
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in IMPORTANT_EXTENSIONS


def make_rich_tree(dir_path: Path, tree: Tree, max_depth: int, 
                   current_depth: int = 0, show_all: bool = False) -> None:
    """Рекурсивно строит дерево с использованием rich."""
    if current_depth >= max_depth:
        return
    
    try:
        # Получаем список элементов, сортируем: сначала папки, потом файлы
        entries = sorted(os.listdir(dir_path), 
                         key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
    except PermissionError:
        tree.add("[red][Permission denied][/]")
        return
    except OSError as e:
        tree.add(f"[red][Error: {str(e)}][/]")
        return
    
    entries_count = len(entries)
    for idx, entry in enumerate(entries):
        # Пропускаем исключенные элементы
        if entry in EXCLUDE_DIRS or entry in EXCLUDE_FILES:
            continue
        
        path = dir_path / entry
        is_last = (idx == entries_count - 1)
        
        if os.path.isdir(path):
            # Добавляем папку
            branch = tree.add(f"[bold blue]{entry}/[/]")
            make_rich_tree(path, branch, max_depth, current_depth + 1, show_all)
        else:
            # Добавляем файл, если он важен или включен режим --all
            if is_important_file(entry, show_all):
                tree.add(entry)


def make_simple_tree(dir_path: Path, prefix: str = "", 
                     max_depth: int = 10, current_depth: int = 0, 
                     show_all: bool = False, is_last_item: bool = True) -> None:
    """Рекурсивно строит дерево без rich (простой текстовый вывод)."""
    if current_depth >= max_depth:
        return
    
    try:
        entries = sorted(os.listdir(dir_path), 
                         key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
    except PermissionError:
        print(f"{prefix}[Permission denied]")
        return
    except OSError as e:
        print(f"{prefix}[Error: {str(e)}]")
        return
    
    # Фильтруем исключенные элементы
    filtered_entries = []
    for entry in entries:
        if entry in EXCLUDE_DIRS or entry in EXCLUDE_FILES:
            continue
        path = dir_path / entry
        if os.path.isdir(path):
            filtered_entries.append(entry)
        elif is_important_file(entry, show_all):
            filtered_entries.append(entry)
    
    entries_count = len(filtered_entries)
    
    for idx, entry in enumerate(filtered_entries):
        is_last = (idx == entries_count - 1)
        path = dir_path / entry
        
        # Определяем префикс для текущего элемента
        if is_last_item:
            connector = "└── " if is_last else "├── "
        else:
            connector = "    " if is_last else "│   "
        
        current_prefix = prefix + connector
        
        if os.path.isdir(path):
            print(f"{current_prefix}{entry}/")
            # Определяем префикс для следующих уровней
            next_prefix = prefix + ("    " if is_last else "│   ")
            make_simple_tree(path, next_prefix, max_depth, current_depth + 1, 
                           show_all, is_last_item and is_last)
        else:
            print(f"{current_prefix}{entry}")


def print_project_info(start_path: Path) -> None:
    """Выводит информацию о проекте Django."""
    print(f"\n📁 Проект: [bold green]{start_path.name}[/]" if RICH_AVAILABLE else f"\nПроект: {start_path.name}")
    
    # Проверяем, Django ли это
    manage_py = start_path / "manage.py"
    if manage_py.exists():
        print("🚀 Тип: Django проект" if RICH_AVAILABLE else "Тип: Django проект")
    
    # Считаем файлы по типам
    py_files = list(start_path.rglob("*.py"))
    html_files = list(start_path.rglob("*.html"))
    json_files = list(start_path.rglob("*.json"))
    
    if RICH_AVAILABLE:
        print(f"📊 Файлы: {len(py_files)} .py, {len(html_files)} .html, {len(json_files)} .json")
    else:
        print(f"Файлы: {len(py_files)} .py, {len(html_files)} .html, {len(json_files)} .json")


def main():
    parser = argparse.ArgumentParser(
        description="Отображение структуры проекта",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "-d", "--depth",
        type=int,
        default=10,
        help="Глубина отображения (по умолчанию: 10, без ограничений)"
    )
    
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Показать все файлы (не только важные)"
    )
    
    parser.add_argument(
        "-p", "--path",
        type=str,
        default=".",
        help="Путь к корневой папке (по умолчанию: текущая)"
    )
    
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Не использовать rich для вывода (даже если установлен)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Показать информацию о проекте"
    )
    
    args = parser.parse_args()
    
    # Проверяем путь
    start_path = Path(args.path).resolve()
    if not start_path.exists():
        print(f"Ошибка: путь '{start_path}' не существует")
        sys.exit(1)
    
    # Показываем информацию о проекте
    if args.info or not RICH_AVAILABLE or args.no_rich:
        print_project_info(start_path)
    
    # Выбираем метод отображения
    use_rich = RICH_AVAILABLE and not args.no_rich
    
    if use_rich:
        # Используем rich для красивого вывода
        tree = Tree(f"[bold green]{start_path.name}/[/]")
        make_rich_tree(start_path, tree, args.depth, 0, args.all)
        print(tree)
    else:
        # Простой текстовый вывод
        print(f"{start_path.name}/")
        make_simple_tree(start_path, "", args.depth, 0, args.all, True)
    
    # Предупреждение о режиме
    if not args.all and not use_rich:
        print("\nℹ️  Для отображения всех файлов используйте флаг --all")
    
    if not RICH_AVAILABLE and not args.no_rich:
        print("\n💡 Установите 'rich' для красивого вывода: pip install rich")


if __name__ == "__main__":
    main()