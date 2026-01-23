from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название места")
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    address = models.CharField(max_length=200, verbose_name="Адрес", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        db_table = 'network_location'
        verbose_name = 'Местонахождение'
        verbose_name_plural = 'Местонахождения'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class NetworkEquipment(models.Model):
    # Определяем choices как константы
    TYPE_CHOICES = [
        ('router', 'Маршрутизатор'),
        ('switch', 'Коммутатор'),
        ('firewall', 'Файрвол'),
        ('server', 'Сервер'),
        ('access_point', 'Точка доступа'),
        ('modem', 'Модем'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активно'),
        ('backup', 'Резерв'),
        ('repair', 'В ремонте'),
        ('decommissioned', 'Списано'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название")
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='switch',
        verbose_name="Тип оборудования"
    )
    model = models.CharField(max_length=100, verbose_name="Модель", blank=True, null=True)
    serial_number = models.CharField(max_length=100, verbose_name="Серийный номер", blank=True, null=True)
    inventory_number = models.CharField(max_length=100, verbose_name="Инвентарный номер", blank=True, null=True)
    
    # Связь с Location
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        verbose_name="Местонахождение",
        blank=True,
        null=True
    )
    
    # Поля для размещения в стойке
    rack = models.IntegerField(verbose_name="Стойка", blank=True, null=True)
    unit = models.IntegerField(verbose_name="Юнит", blank=True, null=True)
    
    # Сетевые параметры
    ip_address = models.GenericIPAddressField(protocol='IPv4', verbose_name="IP-адрес", blank=True, null=True)
    mac_address = models.CharField(max_length=17, verbose_name="MAC-адрес", blank=True, null=True)
    
    # Статус оборудования
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус"
    )
    
    # Дополнительная информация
    notes = models.TextField(verbose_name="Примечания", blank=True, null=True)
    
    # Даты создания и обновления
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        db_table = 'network_networkequipment'
        verbose_name = 'Сетевое оборудование'
        verbose_name_plural = 'Сетевое оборудование'
    
    def __str__(self):
        return self.name


# (Остальные модели пока оставляем как есть)
class NetworkDevice(models.Model):
    # Зарезервировано для будущего использования
    name = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'network_networkdevice'


class Subnet(models.Model):
    # Зарезервировано для будущего использования
    name = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'network_subnet'