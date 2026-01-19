from django.db import models
from django.utils import timezone
from equipments.models import Equipment

class PrinterCheck(models.Model):
    """Старая модель для обратной совместимости"""
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'Принтер'},
        related_name='printer_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name = "Проверка принтера"
        verbose_name_plural = "Проверки принтеров"
    
    def __str__(self):
        status = "✅ Онлайн" if self.is_online else "❌ Офлайн"
        return f"{self.printer} - {status} ({self.checked_at:%H:%M})"

# 1. Быстрые проверки доступности (каждые 5 минут)
class PrinterStatusCheck(models.Model):
    """
    Для частых проверок доступности
    Хранится 24-48 часов, затем агрегируется
    """
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='status_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, blank=True)  # в мс
    ping_success = models.BooleanField(default=False)
    http_success = models.BooleanField(default=False)
    snmp_success = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['printer', '-checked_at']),
            models.Index(fields=['checked_at']),
        ]
        verbose_name = "Быстрая проверка"
        verbose_name_plural = "Быстрые проверки"

# 2. Детальная проверка (раз в день/неделю)
class PrinterDetailCheck(models.Model):
    """
    Подробная проверка с данными о расходниках
    Выполняется реже (раз в день или при проблемах)
    """
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='detail_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    
    STATUS_CHOICES = [
        ('online', 'В сети'),
        ('offline', 'Не в сети'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
        ('sleep', 'Спящий режим'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Основные счетчики
    total_pages = models.IntegerField(null=True, blank=True)
    color_pages = models.IntegerField(null=True, blank=True)
    monochrome_pages = models.IntegerField(null=True, blank=True)
    
    # Уровни расходников (0-100%)
    black_toner = models.IntegerField(null=True, blank=True)
    cyan_toner = models.IntegerField(null=True, blank=True)
    magenta_toner = models.IntegerField(null=True, blank=True)
    yellow_toner = models.IntegerField(null=True, blank=True)
    
    # Остальные данные - в JSON для гибкости
    extra_data = models.JSONField(default=dict, blank=True)
    # Может содержать: серийный номер, версию прошивки, ошибки и т.д.
    
    # Была ли проверка успешной
    check_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name = "Детальная проверка"
        verbose_name_plural = "Детальные проверки"

# 3. Текущее состояние (обновляется при каждой проверке)
class PrinterCurrentStatus(models.Model):
    """
    Текущее состояние принтера - всегда актуальные данные
    Обновляется при каждой проверке любого типа
    """
    printer = models.OneToOneField(
        Equipment,
        on_delete=models.CASCADE,
        related_name='current_status'
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    # Быстрый статус (из PrinterStatusCheck)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    
    # Детальный статус (из PrinterDetailCheck)
    status = models.CharField(max_length=20, choices=PrinterDetailCheck.STATUS_CHOICES, default='offline')
    
    # Актуальные данные о расходниках
    black_toner_level = models.IntegerField(null=True, blank=True)
    cyan_toner_level = models.IntegerField(null=True, blank=True)
    magenta_toner_level = models.IntegerField(null=True, blank=True)
    yellow_toner_level = models.IntegerField(null=True, blank=True)
    total_pages = models.IntegerField(null=True, blank=True)
    
    # Ошибки и предупреждения
    has_errors = models.BooleanField(default=False)
    has_warnings = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)
    
    # Статистика
    uptime_24h = models.FloatField(default=0.0)  # % за последние 24 часа
    last_successful_check = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Текущий статус"
        verbose_name_plural = "Текущие статусы"
    
    def update_from_status_check(self, check):
        """Обновить из быстрой проверки"""
        self.is_online = check.is_online
        self.last_seen = check.checked_at if check.is_online else self.last_seen
        self.response_time = check.response_time
        self.status = 'online' if check.is_online else 'offline'
        self.last_updated = timezone.now()
        
        if check.is_online:
            self.last_successful_check = check.checked_at
        
        self.save()
    
    def update_from_detail_check(self, check):
        """Обновить из детальной проверки"""
        if check.check_successful:
            self.black_toner_level = check.black_toner
            self.cyan_toner_level = check.cyan_toner
            self.magenta_toner_level = check.magenta_toner
            self.yellow_toner_level = check.yellow_toner
            self.total_pages = check.total_pages
            self.status = check.status
            self.last_updated = timezone.now()
            self.save()