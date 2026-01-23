from django.core.management.base import BaseCommand
from printer_monitor.services import PrinterMonitorService

class Command(BaseCommand):
    help = 'Проверяет все принтеры'
    
    def handle(self, *args, **options):
        self.stdout.write("🖨️ Начинаю проверку принтеров...")
        
        results = PrinterMonitorService.check_all_printers()
        
        online = sum(1 for r in results if r['result']['online'])
        offline = len(results) - online
        
        self.stdout.write(f"✅ Проверено: {len(results)} принтеров")
        self.stdout.write(f"✅ Онлайн: {online}")
        self.stdout.write(f"❌ Офлайн: {offline}")