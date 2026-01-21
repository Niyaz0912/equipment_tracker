from django.db import models
from django.utils import timezone
from equipments.models import Equipment
import requests
from bs4 import BeautifulSoup
import re


class PrinterCheck(models.Model):
    """Старая модель для обратной совместимости"""
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'printer'},  # Исправлено: 'printer' вместо 'Принтер'
        related_name='printer_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name = "Проверка принтера"
        verbose_name_plural = "Проверки принтеров"
        indexes = [
            models.Index(fields=['printer', '-checked_at']),
            models.Index(fields=['checked_at']),
            models.Index(fields=['is_online']),
        ]
    
    def __str__(self):
        status = "✅ Онлайн" if self.is_online else "❌ Офлайн"
        return f"{self.printer} - {status} ({self.checked_at:%H:%M})"
    
    def get_status_display(self) -> str:
        """Возвращает человекочитаемый статус"""
        return "В сети" if self.is_online else "Не в сети"


class PrinterCurrentStatus(models.Model):
    """
    Текущее состояние принтера - всегда актуальные данные
    """
    printer = models.OneToOneField(
        Equipment,
        on_delete=models.CASCADE,
        related_name='current_status'
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    # Быстрый статус
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    
    # Детальный статус
    STATUS_CHOICES = [
        ('online', 'В сети'),
        ('offline', 'Не в сети'),
        ('warning', 'Предупреждение'),
        ('error', 'Ошибка'),
        ('sleep', 'Спящий режим'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    
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
    uptime_24h = models.FloatField(default=0.0)
    last_successful_check = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Текущий статус"
        verbose_name_plural = "Текущие статусы"
        indexes = [
            models.Index(fields=['is_online']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.printer} - {self.get_status_display()}"
    
    def get_status_display(self) -> str:
        """Возвращает человекочитаемый статус"""
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')
    
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
    
    @property
    def is_problematic(self) -> bool:
        """Есть ли проблемы у принтера"""
        if not self.is_online:
            return True
        if self.has_errors:
            return True
        if self.status in ['error', 'offline']:
            return True
        return False