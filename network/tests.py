from django.test import TestCase
from django.urls import reverse
from .models import Location, NetworkEquipment

class NetworkModelsTest(TestCase):
    """Тесты моделей"""
    
    def setUp(self):
        """Создаем тестовые данные"""
        self.location = Location.objects.create(
            name='Тестовая серверная',
            description='Для тестирования',
            address='ул. Тестовая, 1'
        )
        
        self.equipment = NetworkEquipment.objects.create(
            name='Тестовый коммутатор',
            type='switch',
            model='Cisco 2960',
            status='active',
            location=self.location,
            ip_address='192.168.1.100'
        )
    
    def test_location_creation(self):
        """Проверка создания Location"""
        self.assertEqual(self.location.name, 'Тестовая серверная')
        self.assertEqual(str(self.location), 'Тестовая серверная')
        self.assertTrue(isinstance(self.location, Location))
    
    def test_equipment_creation(self):
        """Проверка создания NetworkEquipment"""
        self.assertEqual(self.equipment.name, 'Тестовый коммутатор')
        self.assertEqual(self.equipment.type, 'switch')
        self.assertEqual(self.equipment.status, 'active')
        self.assertEqual(self.equipment.location.name, 'Тестовая серверная')
        self.assertEqual(str(self.equipment), 'Тестовый коммутатор')
    
    def test_equipment_status_choices(self):
        """Проверка корректности статусов"""
        valid_statuses = ['active', 'backup', 'repair', 'decommissioned']
        self.assertIn(self.equipment.status, valid_statuses)
    
    def test_equipment_type_choices(self):
        """Проверка корректности типов оборудования"""
        valid_types = ['router', 'switch', 'firewall', 'server', 'access_point', 'modem', 'other']
        self.assertIn(self.equipment.type, valid_types)


class NetworkViewsTest(TestCase):
    """Тесты представлений"""
    
    def setUp(self):
        """Создаем тестовые данные"""
        self.location = Location.objects.create(
            name='Тестовая локация',
            address='Тестовый адрес'
        )
        
        self.equipment = NetworkEquipment.objects.create(
            name='Тестовое оборудование',
            type='switch',
            status='active',
            location=self.location
        )
    
    def test_equipment_list_view(self):
        """Тест главной страницы оборудования"""
        response = self.client.get('/network/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'network/equipment_list.html')
        self.assertContains(response, 'Тестовое оборудование')
    
    def test_equipment_detail_view(self):
        """Тест детальной страницы оборудования"""
        response = self.client.get(f'/network/equipment/{self.equipment.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'network/equipment_detail.html')
        self.assertContains(response, 'Тестовое оборудование')
    
    def test_equipment_list_empty(self):
        """Тест пустого списка оборудования"""
        # Удаляем все оборудование
        NetworkEquipment.objects.all().delete()
        response = self.client.get('/network/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Сетевое оборудование не найдено')
    
    def test_search_functionality(self):
        """Тест поиска оборудования"""
        response = self.client.get('/network/?search=Тестовое')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое оборудование')
    
    def test_status_filter(self):
        """Тест фильтрации по статусу"""
        response = self.client.get('/network/?status=active')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое оборудование')
    
    def test_admin_links(self):
        """Тест доступности админ-ссылок"""
        # Создаем суперпользователя
        from django.contrib.auth.models import User
        User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.client.login(username='admin', password='password')
        
        # Проверяем доступность админки
        response = self.client.get('/admin/network/networkequipment/')
        self.assertEqual(response.status_code, 200)


class NetworkURLsTest(TestCase):
    """Тесты URL-адресов"""
    
    def test_urls_exist(self):
        """Проверка существования основных URL"""
        urls = [
            '/network/',
            '/network/equipment/',
            '/network/equipment/create/',
        ]
        
        for url in urls:
            response = self.client.get(url)
            # Может быть 200 или 302 (редирект на логин для create)
            self.assertIn(response.status_code, [200, 302])
    
    def test_equipment_urls(self):
        """Тест URL для конкретного оборудования"""
        equipment = NetworkEquipment.objects.create(
            name='URL тест',
            type='router',
            status='active'
        )
        
        urls = [
            f'/network/equipment/{equipment.id}/',
            f'/network/equipment/{equipment.id}/edit/',
            f'/network/equipment/{equipment.id}/delete/',
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 302])


class NetworkFormsTest(TestCase):
    """Тесты форм (минимальные)"""
    
    def test_equipment_form_valid(self):
        """Тест валидной формы"""
        from .forms import NetworkEquipmentForm
        
        location = Location.objects.create(name='Форма тест')
        
        form_data = {
            'name': 'Тест через форму',
            'type': 'switch',
            'status': 'active',
            'location': location.id,
        }
        
        form = NetworkEquipmentForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Сохраняем
        equipment = form.save()
        self.assertEqual(equipment.name, 'Тест через форму')
        self.assertEqual(equipment.type, 'switch')
    
    def test_equipment_form_invalid(self):
        """Тест невалидной формы (без имени)"""
        from .forms import NetworkEquipmentForm
        
        form_data = {
            'type': 'switch',
            'status': 'active',
            # Нет обязательного поля 'name'
        }
        
        form = NetworkEquipmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class NetworkTemplateTest(TestCase):
    """Тесты шаблонов"""
    
    def setUp(self):
        self.equipment = NetworkEquipment.objects.create(
            name='Шаблон тест',
            type='switch',
            status='active',
            ip_address='192.168.1.50'
        )
    
    def test_template_context(self):
        """Проверка контекста шаблона"""
        response = self.client.get('/network/')
        
        # Проверяем наличие ключевых данных в контексте
        self.assertIn('equipments', response.context)
        self.assertIn('status_stats', response.context)
        self.assertIn('search_query', response.context)
        
        # Проверяем оборудование в контексте
        equipments = response.context['equipments']
        self.assertEqual(equipments.count(), 1)
        self.assertEqual(equipments.first().name, 'Шаблон тест')
    
    def test_template_content(self):
        """Проверка содержимого шаблона"""
        response = self.client.get('/network/')
        
        # Ключевые элементы на странице
        content = response.content.decode()
        
        self.assertIn('Шаблон тест', content)
        self.assertIn('192.168.1.50', content)
        self.assertIn('Активно', content)  # Статус
        self.assertIn('Поиск', content)  # Поле поиска
        self.assertIn('Добавить оборудование', content)  # Кнопка


# Минимальный тест для быстрой проверки
class QuickSmokeTest(TestCase):
    """Дымовой тест - быстрая проверка работоспособности"""
    
    def test_everything_works(self):
        """Проверяем, что всё вообще работает"""
        # 1. Модели
        location = Location.objects.create(name='Дымовой тест')
        equipment = NetworkEquipment.objects.create(
            name='Дымовое оборудование',
            type='switch',
            status='active',
            location=location
        )
        
        # 2. Представления
        response = self.client.get('/network/')
        self.assertEqual(response.status_code, 200)
        
        # 3. Детальная страница
        detail_response = self.client.get(f'/network/equipment/{equipment.id}/')
        self.assertIn(detail_response.status_code, [200, 302])
        
        # 4. Админка (попытка доступа)
        admin_response = self.client.get('/admin/')
        self.assertIn(admin_response.status_code, [200, 302])
        
        print("✅ Дымовой тест пройден! Базовая функциональность работает.")