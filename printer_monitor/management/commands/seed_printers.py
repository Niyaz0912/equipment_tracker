# printer_monitor/management/commands/seed_printers.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from equipments.models import Equipment, Department
from printer_monitor.models import PrinterCheck, PrinterCurrentStatus
import random

class Command(BaseCommand):
    def handle(self, *args, **options):
        departments = []
        for name in ['Бухгалтерия', 'Отдел продаж', 'Склад', 'ИТ-отдел']:
            dept, _ = Department.objects.get_or_create(name=name)
            departments.append(dept)
        
        for i in range(1, 6):
            mc_number = f'PRN{i:03d}'
            ip_address = f'192.168.1.{100 + i}' if i % 2 == 0 else None
            
            printer = Equipment.objects.create(
                mc_number=mc_number,
                type='printer',
                brand='HP' if i % 2 == 0 else 'Canon',
                model=f'LaserJet {i}00' if i % 2 == 0 else f'i-SENSYS MF{i}00',
                ip_address=ip_address,
                assigned_department=random.choice(departments),
                status='issued'
            )
            
            is_online = bool(ip_address) and random.random() > 0.3
            PrinterCurrentStatus.objects.create(
                printer=printer,
                is_online=is_online,
                status='online' if is_online else 'offline',
                last_updated=timezone.now(),
            )
            
            # ДОБАВЛЯЕМ notes (пустую строку если нет заметок)
            PrinterCheck.objects.create(
                printer=printer,
                is_online=is_online,
                response_time=random.randint(50, 200) if is_online else None,
                notes=''  # <-- ДОБАВИЛИ ЭТО
            )
            
            print(f"✅ Создан: {printer}")
        
        print(f"\n📊 Принтеров: {Equipment.objects.filter(type='printer').count()}")