# network/apps.py
import os
from django.apps import AppConfig

class NetworkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network'
    
    def ready(self):
        # Запускаем только в основном процессе, не в reloader
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
        
        # Импортируем здесь чтобы избежать circular imports
        from apscheduler.schedulers.background import BackgroundScheduler
        from .services.scanner import scanner
        
        def scan_network_background():
            """Фоновая задача сканирования"""
            print("🔄 Запускаю фоновое сканирование сети...")
            try:
                network = scanner.detect_network()
                devices = scanner.simple_scan(network)
                print(f"✅ Фоновое сканирование завершено. Найдено: {len(devices)} устройств")
                
                # Можно сохранить в кэш или специальную модель
                from django.core.cache import cache
                cache.set('last_background_scan', {
                    'devices': devices,
                    'network': network,
                    'timestamp': 'время'
                }, timeout=60*60*24)  # Храним сутки
                
            except Exception as e:
                print(f"❌ Ошибка фонового сканирования: {e}")
        
        try:
            scheduler = BackgroundScheduler()
            # Сканируем каждые 6 часов, первый запуск через 30 секунд после старта
            scheduler.add_job(
                scan_network_background,
                'interval',
                hours=6,
                id='network_scan',
                replace_existing=True
            )
            
            # Запускаем немедленно для теста (или через 30 секунд)
            scheduler.add_job(
                scan_network_background,
                'date',
                run_date='now',
                id='initial_scan'
            )
            
            scheduler.start()
            print("✅ Планировщик фонового сканирования запущен")
            
        except Exception as e:
            print(f"❌ Ошибка запуска планировщика: {e}")