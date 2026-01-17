# equipments/models.py
from django.db import models
from django.urls import reverse
from employees.models import Employee, Department  # добавляем импорт Department

class Equipment(models.Model):
    TYPE_CHOICES = [
        ('laptop', 'Ноутбук'),
        ('pc', 'Компьютер'),
        ('monitor', 'Монитор'),
        ('keyboard', 'Клавиатура'),
        ('mouse', 'Мышь'),
        ('printer', 'Принтер'),
        ('scanner', 'Сканер'),
        ('headphones', 'Наушники'),
        ('phone', 'Телефон'),
        ('webcam', 'Веб-камера'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'На складе'),
        ('issued', 'Выдано'),
        ('broken', 'Сломан'),
        ('repair', 'В ремонте'),
        ('written_off', 'Списан'),
    ]
    
    mc_number = models.CharField('Номер МЦ', max_length=20, db_index=True, blank=True, null=True)
    type = models.CharField('Тип', max_length=50, choices=TYPE_CHOICES)
    brand = models.CharField('Марка', max_length=100, blank=True)
    model = models.CharField('Модель', max_length=100, blank=True)
    
    # НОВОЕ ПОЛЕ: IP адрес для сетевых принтеров
    ip_address = models.CharField(
        'IP адрес',
        max_length=15,  # IPv4: 255.255.255.255
        blank=True,
        null=True,
        help_text='IPv4 адрес для сетевых принтеров (например: 192.168.1.100)'
    )
    
    # Закрепление за сотрудником
    assigned_to = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Закреплено за сотрудником',
        related_name='assigned_equipment'
    )
    
    # НОВОЕ: Закрепление за отделом
    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Закреплено за отделом',
        related_name='department_equipment'
    )
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='issued')
    purchase_date = models.DateField('Дата покупки', null=True, blank=True)
    warranty_until = models.DateField('Гарантия до', null=True, blank=True)
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # НОВЫЙ МЕТОД: Проверка является ли принтер сетевым
    @property
    def is_network_printer(self):
        """Возвращает True если это принтер и у него есть IP адрес"""
        return self.type == 'printer' and bool(self.ip_address)
    
    # НОВЫЙ МЕТОД: Валидация IP адреса (опционально)
    def clean(self):
        """Валидация данных перед сохранением"""
        super().clean()
        
        if self.ip_address:
            # Проверяем что IP указан только для принтеров
            if self.type != 'printer':
                raise ValidationError({'ip_address': 'IP адрес можно указывать только для принтеров'})
            
            # Простая валидация формата IPv4
            try:
                ipaddress.IPv4Address(self.ip_address)
            except ipaddress.AddressValueError:
                raise ValidationError({'ip_address': 'Введите корректный IPv4 адрес'})
    
    # НОВЫЙ МЕТОД: Отображение информации о сетевом принтере
    @property
    def network_info(self):
        """Информация о сетевом подключении"""
        if self.type == 'printer':
            if self.ip_address:
                return f"🖨️ Сетевой принтер ({self.ip_address})"
            else:
                return f"🖨️ Локальный принтер (USB)"
        return None
    
    # Обновляем __str__ чтобы показывать IP для принтеров
    def __str__(self):
        if self.mc_number:
            equipment_info = f"{self.mc_number} - {self.get_type_display()}"
        else:
            equipment_info = f"Без МЦ - {self.get_type_display()}"
            
        if self.brand:
            equipment_info += f" {self.brand}"
        if self.model:
            equipment_info += f" {self.model}"
        
        # Показываем IP для сетевых принтеров
        if self.type == 'printer' and self.ip_address:
            equipment_info += f" [{self.ip_address}]"
        
        # Показываем кому/чему закреплено
        if self.assigned_to:
            equipment_info += f" ({self.assigned_to.last_name})"
        elif self.assigned_department:
            equipment_info += f" [{self.assigned_department.name}]"
        
        return equipment_info
    
    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'
        ordering = ['mc_number']
        indexes = [
            models.Index(fields=['mc_number']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        if self.mc_number:
            equipment_info = f"{self.mc_number} - {self.get_type_display()}"
        else:
            equipment_info = f"Без МЦ - {self.get_type_display()}"
            
        if self.brand:
            equipment_info += f" {self.brand}"
        if self.model:
            equipment_info += f" {self.model}"
        
        # Показываем кому/чему закреплено
        if self.assigned_to:
            equipment_info += f" ({self.assigned_to.last_name})"
        elif self.assigned_department:
            equipment_info += f" [{self.assigned_department.name}]"
        
        return equipment_info
    
    def get_absolute_url(self):
        return reverse('equipments:detail', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        """Полное название оборудования"""
        parts = []
        if self.brand:
            parts.append(self.brand)
        if self.model:
            parts.append(self.model)
        return " ".join(parts) if parts else "Не указано"
    
    @property
    def is_assigned(self):
        """Проверка, закреплено ли оборудование"""
        return self.assigned_to is not None or self.assigned_department is not None
    
    @property
    def assigned_to_display(self):
        """Отображение кому/чему закреплено оборудование"""
        if self.assigned_to:
            return f"Сотрудник: {self.assigned_to.full_name}"
        elif self.assigned_department:
            return f"Отдел: {self.assigned_department.name}"
        else:
            return "Не закреплено"
    
    @property
    def display_mc(self):
        """Отображение МЦ номера (или текста если нет)"""
        return self.mc_number if self.mc_number else "Без МЦ"