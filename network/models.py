# network/models.py
from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    address = models.CharField(max_length=200, blank=True, verbose_name="Адрес")
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'network_location'  # Явно указываем имя таблицы

class NetworkEquipment(models.Model):
    TYPE_CHOICES = [
        ('server', 'Сервер'),
        ('router', 'Маршрутизатор'),
        ('switch', 'Коммутатор'),
        ('access_point', 'Точка доступа'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('inactive', 'Неактивен'),
        ('maintenance', 'Обслуживается'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Тип")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP-адрес")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, 
                                 verbose_name="Место размещения")
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'network_networkequipment'