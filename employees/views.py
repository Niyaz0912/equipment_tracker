# employees/views.py
import pandas as pd
from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from .models import Employee, Department

def employee_list(request):
    """Список сотрудников"""
    employees = Employee.objects.select_related('department').filter(is_active=True)
    
    # Фильтрация по отделу
    department_filter = request.GET.get('department')
    if department_filter:
        employees = employees.filter(department_id=department_filter)
    
    # Получаем все отделы для фильтра
    departments = Department.objects.all()
    
    context = {
        'employees': employees,
        'departments': departments,
        'department_filter': department_filter,
    }
    return render(request, 'employees/employee_list.html', context)

def employee_detail(request, pk):
    """Детальная информация о сотруднике"""
    employee = get_object_or_404(Employee.objects.select_related('department'), pk=pk)
    
    # Оборудование сотрудника
    from equipments.models import Equipment
    equipment = Equipment.objects.filter(assigned_to=employee).select_related('assigned_to')
    
    # История выдачи (если нужно)
    from history.models import EquipmentHistory
    history = EquipmentHistory.objects.filter(employee=employee).select_related('equipment')
    
    context = {
        'employee': employee,
        'equipment': equipment,
        'history': history,
        'equipment_count': equipment.count(),
    }
    return render(request, 'employees/employee_detail.html', context)


def export_employees_excel(request):
    """Экспорт сотрудников в Excel"""
    employees = Employee.objects.select_related('department').filter(is_active=True)
    
    # Фильтрация
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