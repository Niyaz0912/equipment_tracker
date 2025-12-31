# employees/models.py
from django.db import models

class Department(models.Model):
    name = models.CharField('Название отдела', max_length=100, unique=True)
    short_name = models.CharField('Короткое название', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
    
    def __str__(self):
        return self.name

class Employee(models.Model):
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Отдел')
    position = models.CharField('Должность', max_length=100, blank=True)
    is_active = models.BooleanField('Работает', default=True)
    
    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()
    
    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()