# excel_export/views.py
import pandas as pd
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Q

def export_excel(request):
    """
    Универсальный экспорт данных в Excel.
    
    Параметры:
    - model: 'equipment' или 'employee' (обязательный)
    - Все остальные параметры фильтрации из исходной страницы
    """
    model_type = request.GET.get('model')
    
    if not model_type:
        # Можно вернуть ошибку или шаблон для выбора
        return HttpResponse("Ошибка: не указан параметр model", status=400)
    
    if model_type == 'equipment':
        return export_equipment(request)
    elif model_type == 'employee':
        return export_employees(request)
    else:
        return HttpResponse(f"Ошибка: неизвестный тип модели '{model_type}'", status=400)


def export_equipment(request):
    """Экспорт оборудования (логика из equipments/views.py)"""
    from equipments.models import Equipment
    from employees.models import Department
    
    equipments = Equipment.objects.select_related('assigned_to', 'assigned_to__department', 'assigned_department').all()
    
    # Фильтрация (ТОЧНО ТАК ЖЕ как в equipment_list)
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


def export_employees(request):
    """Экспорт сотрудников (логика из employees/views.py)"""
    from employees.models import Employee, Department
    
    employees = Employee.objects.select_related('department').filter(is_active=True)
    
    # Фильтрация (ТОЧНО ТАК ЖЕ как в employee_list)
    department_filter = request.GET.get('department')
    
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # Создаем DataFrame
    data = []
    for emp in employees:
        # Считаем оборудование сотрудника
        from equipments.models import Equipment
        equipment_count = Equipment.objects.filter(assigned_to=emp).count()
        
        data.append({
            'Фамилия': emp.last_name,
            'Имя': emp.first_name,
            'Отчество': emp.middle_name or '',
            'Отдел': emp.department.name if emp.department else '',
            'Должность': emp.position or '',
            'Количество оборудования': equipment_count,
            'Статус': 'Работает' if emp.is_active else 'Уволен',
        })
    
    df = pd.DataFrame(data)
    
    # Создаем имя файла
    filename = f'employees_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # Создаем HttpResponse с Excel файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Сохраняем в HttpResponse
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Сотрудники')
    
    return response
