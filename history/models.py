# history/models.py
from django.db import models
from equipments.models import Equipment
from employees.models import Employee

class EquipmentHistory(models.Model):
    ACTION_CHOICES = [
        ('issue', 'Выдача'),
        ('return', 'Возврат'),
        ('repair', 'Отправка в ремонт'),
        ('write_off', 'Списание'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='history_records')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    action = models.CharField('Действие', max_length=20, choices=ACTION_CHOICES, default='issue')
    date = models.DateField('Дата')
    notes = models.TextField('Примечания', blank=True)
    created_by = models.CharField('Кем внесено', max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'История оборудования'
        verbose_name_plural = 'История оборудования'
        ordering = ['-date', '-id']
    
    def __str__(self):
        return f"{self.equipment.mc_number} - {self.get_action_display()} - {self.employee.full_name}"