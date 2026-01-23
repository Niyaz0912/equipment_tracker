# printer_monitor/models.py - ТОЛЬКО МОДЕЛИ
from django.db import models
from django.utils import timezone
from equipments.models import Equipment

class PrinterCheck(models.Model):
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'printer'},
        related_name='printer_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-checked_at']
    
    def __str__(self):
        status = "✅ Онлайн" if self.is_online else "❌ Офлайн"
        return f"{self.printer} - {status} ({self.checked_at:%H:%M})"


class PrinterCurrentStatus(models.Model):
    printer = models.OneToOneField(
        Equipment,
        on_delete=models.CASCADE,
        related_name='current_status'
    )
    last_updated = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    
    STATUS_CHOICES = [
        ('online', 'В сети'),
        ('offline', 'Не в сети'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    
    class Meta:
        verbose_name = "Текущий статус"
        verbose_name_plural = "Текущие статусы"
    
    def __str__(self):
        return f"{self.printer} - {self.get_status_display()}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Неизвестно')