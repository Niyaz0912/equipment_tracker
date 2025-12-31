# employees/admin.py
from django.contrib import admin
from .models import Department, Employee

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'department', 'position', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('last_name', 'first_name', 'middle_name')
    ordering = ('last_name', 'first_name')
    
    # Убираем email и телефон из формы
    fields = ('last_name', 'first_name', 'middle_name', 'department', 'position', 'is_active')