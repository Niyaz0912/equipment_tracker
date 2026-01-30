from django.db import models

PURPOSE_CHOICES = [
    ('client', 'Клиентская сеть'),
    ('server', 'Серверная сеть'),
    ('infrastructure', 'Сетевая инфраструктура'),
    ('management', 'Управление'),
    ('dmz', 'DMZ'),
    ('wireless', 'Беспроводная сеть'),
    ('other', 'Другое'),
]

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
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    
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
    
    scan_source = models.CharField(
        max_length=50,
        verbose_name="Источник обнаружения",
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'network_networkequipment'
        verbose_name = 'Сетевое оборудование'
        verbose_name_plural = 'Сетевое оборудование'
    
    def __str__(self):
        return self.name


class Subnet(models.Model):
    network = models.CharField("Подсеть", max_length=18, default="192.168.1.0/24")
    description = models.CharField("Описание", max_length=200, default="Нет описания")
    vlan_id = models.IntegerField("VLAN ID", blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    purpose = models.CharField("Назначение", max_length=50, choices=PURPOSE_CHOICES, default="client")
    date_added = models.DateTimeField("Дата добавления", auto_now_add=True)
    added_by = models.CharField("Кем добавлено", max_length=100, default="admin")
    comment = models.TextField("Комментарий", blank=True, default="")
    
    def get_ip_stats(self):
        """Статистика IP адресов в подсети"""
        from ipaddress import ip_network
        
        try:
            # Рассчитываем общее количество адресов в подсети
            network = ip_network(self.network, strict=False)
            total = network.num_addresses - 2  # минус сеть и броадкаст
            
            if total < 0:
                total = 0  # для /32 и /31 подсетей
        except ValueError:
            total = 254  # если ошибка в формате
            
        occupied = self.ipaddress_set.filter(status='occupied').count()
        free = total - occupied if total > occupied else 0
        percent = (occupied / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'occupied': occupied,
            'free': free,
            'percent': percent
        }

    class Meta:
        db_table = 'network_subnet'
    
    def __str__(self):
        return f"{self.network} ({self.description})"        

class IPAddress(models.Model):
    STATUS_CHOICES = [
        ('free', 'Свободен'),
        ('reserved', 'Зарезервирован'),
        ('dynamic', 'DHCP'),
        ('occupied', 'Занят'),
    ]
    
    address = models.CharField("IP-адрес", max_length=15)
    subnet = models.ForeignKey(Subnet, on_delete=models.CASCADE, verbose_name="Подсеть")
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default='free')
    description = models.CharField("Описание", max_length=200, blank=True)
    device = models.ForeignKey(NetworkEquipment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Оборудование")
    mac_address = models.CharField("MAC-адрес", max_length=17, blank=True)
    dns_name = models.CharField("DNS имя", max_length=100, blank=True)
    last_updated = models.DateTimeField("Последнее обновление", auto_now=True)
    note = models.TextField("Заметки", blank=True)
    
    class Meta:
        db_table = 'network_ipaddress'
        verbose_name = 'IP-адрес'
        verbose_name_plural = 'IP-адреса'
        ordering = ['address']
    
    def __str__(self):
        return f"{self.address} ({self.get_status_display()})"