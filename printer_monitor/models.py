from django.db import models
from django.utils import timezone
from equipments.models import Equipment

class PrinterCheck(models.Model):
    """
    Минимальная модель для хранения результатов проверки принтера
    Одна проверка = одна запись
    """
    printer = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        limit_choices_to={'type': 'Принтер'},  # Только принтеры
        related_name='printer_checks'
    )
    checked_at = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, blank=True)  # в секундах
    notes = models.TextField(blank=True)  # Любые дополнительные заметки
    
    class Meta:
        ordering = ['-checked_at']
        verbose_name = "Проверка принтера"
        verbose_name_plural = "Проверки принтеров"
    
    def __str__(self):
        status = "✅ Онлайн" if self.is_online else "❌ Офлайн"
        return f"{self.printer} - {status} ({self.checked_at:%H:%M})"