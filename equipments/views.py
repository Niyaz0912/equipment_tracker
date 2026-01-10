# equipments/views.py
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from .models import Equipment
import pandas as pd
from django.http import HttpResponse
from django.contrib import messages
import os
from datetime import datetime
from django.conf import settings


def equipment_list(request):
    """Список всего оборудования с фильтрами"""
    equipments = Equipment.objects.select_related('assigned_to', 'assigned_to__department', 'assigned_department').all()
    
    from employees.models import Department, Employee
    
    # Фильтрация
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    department_filter = request.GET.get('department')
    assigned_department_filter = request.GET.get('assigned_department')  # НОВОЕ
    employee_filter = request.GET.get('employee')
    
    if status_filter:
        equipments = equipments.filter(status=status_filter)
    
    if type_filter:
        equipments = equipments.filter(type=type_filter)
    
    if department_filter:
        equipments = equipments.filter(assigned_to__department_id=department_filter)
    
    if assigned_department_filter:  # НОВОЕ
        equipments = equipments.filter(assigned_department_id=assigned_department_filter)
    
    if employee_filter:
        equipments = equipments.filter(assigned_to_id=employee_filter)
    
    departments = Department.objects.all()
    employees = Employee.objects.filter(is_active=True)
    
    context = {
        'equipments': equipments,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'department_filter': department_filter,
        'assigned_department_filter': assigned_department_filter,  # НОВОЕ
        'employee_filter': employee_filter,
        'departments': departments,
        'employees': employees,
    }
    return render(request, 'equipments/equipment_list.html', context)


def equipment_search(request):
    """Поиск оборудования"""
    query = request.GET.get('q', '')
    equipments = Equipment.objects.select_related('assigned_to')
    
    if query:
        equipments = equipments.filter(
            Q(mc_number__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(notes__icontains=query) |
            Q(assigned_to__last_name__icontains=query) |
            Q(assigned_to__first_name__icontains=query) |
            Q(assigned_to__middle_name__icontains=query) |  # Добавили
            Q(assigned_department__name__icontains=query)   # Добавили - НЕТ запятой в конце!
        )
    
    context = {
        'equipments': equipments,
        'query': query,
        'results_count': equipments.count(),
    }
    return render(request, 'equipments/equipment_search.html', context)

def equipment_detail(request, pk):
    """Детальная информация об оборудовании"""
    equipment = get_object_or_404(
        Equipment.objects.select_related('assigned_to'),
        pk=pk
    )
    
    # История оборудования (если есть)
    history = equipment.history_records.all().select_related('employee')
    
    context = {
        'equipment': equipment,
        'history': history,
    }
    return render(request, 'equipments/equipment_detail.html', context)

def equipment_import(request):
    """Импорт оборудования из Excel"""
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        
        if not excel_file:
            messages.error(request, 'Пожалуйста, выберите файл для загрузки')
            return render(request, 'equipments/import_export.html')
        
        try:
            # Читаем Excel файл
            df = pd.read_excel(excel_file)
            
            imported = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Получаем данные из строки
                    mc_number = str(row.get('МЦ номер', '')).strip()
                    if mc_number == 'nan' or mc_number == 'None' or not mc_number:
                        mc_number = None
                    
                    # Преобразуем тип оборудования
                    type_mapping = {
                        'ноутбук': 'laptop',
                        'компьютер': 'pc', 
                        'монитор': 'monitor',
                        'клавиатура': 'keyboard',
                        'мышь': 'mouse',
                        'принтер': 'printer',
                        'сканер': 'scanner',
                        'наушники': 'headphones',
                        'телефон': 'phone',
                        'веб-камера': 'webcam',
                    }
                    
                    type_str = str(row.get('Тип', '')).strip().lower()
                    equipment_type = type_mapping.get(type_str, 'other')
                    
                    # Преобразуем статус
                    status_mapping = {
                        'на складе': 'available',
                        'выдано': 'issued',
                        'сломан': 'broken',
                        'в ремонте': 'repair',
                        'списан': 'written_off',
                    }
                    
                    status_str = str(row.get('Статус', '')).strip().lower()
                    status = status_mapping.get(status_str, 'issued')
                    
                    # Ищем сотрудника
                    employee_name = str(row.get('Сотрудник', '')).strip()
                    assigned_to = None
                    
                    if employee_name and employee_name.lower() not in ['nan', 'none', '']:
                        from employees.models import Employee
                        # Пробуем найти сотрудника по ФИО
                        try:
                            last_name = employee_name.split()[0] if employee_name else ''
                            assigned_to = Employee.objects.filter(
                                last_name__icontains=last_name
                            ).first()
                        except:
                            pass
                    
                    # Ищем отдел для закрепления
                    department_name = str(row.get('Отдел', '')).strip()
                    assigned_department = None
                    
                    if department_name and department_name.lower() not in ['nan', 'none', '']:
                        from employees.models import Department
                        assigned_department = Department.objects.filter(
                            name__icontains=department_name
                        ).first()
                    
                    # Создаем оборудование
                    Equipment.objects.create(
                        mc_number=mc_number,
                        type=equipment_type,
                        brand=str(row.get('Марка', '')).strip(),
                        model=str(row.get('Модель', '')).strip(),
                        assigned_to=assigned_to,
                        assigned_department=assigned_department,  # НОВОЕ ПОЛЕ
                        status=status,
                        notes=str(row.get('Примечания', '')).strip(),
                    )
                    
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Строка {index + 2}: {str(e)}")
            
            # Сообщаем о результате
            if imported > 0:
                messages.success(request, f'Успешно импортировано {imported} записей')
            if errors:
                messages.warning(request, f'Ошибки при импорте: {len(errors)} записей')
            
            # Сохраняем ошибки в файл (если есть)
            if errors:
                error_file = os.path.join(settings.EXCEL_FOLDER, f'errors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(errors))
            
            return redirect('equipments:equipment_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при чтении файла: {str(e)}')
    
    return render(request, 'equipments/import_export.html')

# equipments/views.py - добавляем или убеждаемся что есть
def export_equipment_excel(request):
    """Экспорт отфильтрованного оборудования в Excel"""
    from employees.models import Department
    
    equipments = Equipment.objects.select_related('assigned_to', 'assigned_to__department', 'assigned_department').all()
    
    # Фильтрация
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    department_filter = request.GET.get('department')
    assigned_department_filter = request.GET.get('assigned_department')
    employee_filter = request.GET.get('employee')
    search_query = request.GET.get('q')
    
    if status_filter:
        equipments = equipments.filter(status=status_filter)
    
    if type_filter:
        equipments = equipments.filter(type=type_filter)
    
    if department_filter:
        equipments = equipments.filter(assigned_to__department_id=department_filter)
    
    if assigned_department_filter:
        equipments = equipments.filter(assigned_department_id=assigned_department_filter)
    
    if employee_filter:
        equipments = equipments.filter(assigned_to_id=employee_filter)
    
    if search_query:
        equipments = equipments.filter(
            Q(mc_number__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(assigned_to__last_name__icontains=search_query) |
            Q(assigned_to__first_name__icontains=search_query) |
            Q(assigned_department__name__icontains=search_query)
        )
    
    # Создаем DataFrame
    data = []
    for eq in equipments:
        data.append({
            'МЦ номер': eq.mc_number or 'Без МЦ',
            'Тип': eq.get_type_display(),
            'Марка': eq.brand or '',
            'Модель': eq.model or '',
            'Статус': eq.get_status_display(),
            'Сотрудник': eq.assigned_to.full_name if eq.assigned_to else '',
            'Отдел (сотрудника)': eq.assigned_to.department.name if eq.assigned_to and eq.assigned_to.department else '',
            'Закреплено за отделом': eq.assigned_department.name if eq.assigned_department else '',
            'Дата добавления': eq.created_at.strftime('%d.%m.%Y') if eq.created_at else '',
            'Примечания': eq.notes or '',
        })
    
    df = pd.DataFrame(data)
    
    # Создаем имя файла
    filename = f'equipment_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # Создаем HttpResponse с Excel файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Сохраняем в HttpResponse
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Оборудование')
    
    return response

def export_template(request):
    """Скачать шаблон Excel для импорта"""
    # Создаем DataFrame с шаблоном
    data = [
        {
            'МЦ номер': '123456',
            'Тип': 'ноутбук',
            'Марка': 'Dell',
            'Модель': 'Latitude 5420',
            'Сотрудник': 'Иванов Иван',
            'Статус': 'выдано',
            'Примечания': 'Пример записи'
        },
        {
            'МЦ номер': '123457',
            'Тип': 'монитор',
            'Марка': 'Samsung',
            'Модель': 'S24F350',
            'Сотрудник': '',
            'Статус': 'на складе',
            'Примечания': ''
        }
    ]
    
    df = pd.DataFrame(data)
    
    # Создаем HttpResponse с Excel файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_template.xlsx"'
    
    # Сохраняем в HttpResponse
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Шаблон')
        
        # Добавляем лист с подсказками
        hints_data = {
            'Поле': ['МЦ номер', 'Тип', 'Статус', 'Сотрудник'],
            'Допустимые значения': [
                'Любой текст/цифры (обязательное поле)',
                'ноутбук, компьютер, монитор, клавиатура, мышь, принтер, сканер, наушники, телефон, веб-камера',
                'на складе, выдано, сломан, в ремонте, списан',
                'Фамилия сотрудника (необязательно)'
            ]
        }
        hints_df = pd.DataFrame(hints_data)
        hints_df.to_excel(writer, index=False, sheet_name='Подсказки')
    
    return response