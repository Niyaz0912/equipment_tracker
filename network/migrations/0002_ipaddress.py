# Создай новый файл network/migrations/0002_ipaddress.py ВРУЧНУЮ:

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('network', '0001_initial_ip_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=15, verbose_name='IP-адрес')),
                ('status', models.CharField(choices=[('free', 'Свободен'), ('reserved', 'Зарезервирован'), ('dynamic', 'DHCP'), ('occupied', 'Занят')], default='free', max_length=10, verbose_name='Статус')),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='Описание')),
                ('mac_address', models.CharField(blank=True, max_length=17, verbose_name='MAC-адрес')),
                ('dns_name', models.CharField(blank=True, max_length=100, verbose_name='DNS имя')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Последнее обновление')),
                ('note', models.TextField(blank=True, verbose_name='Заметки')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='network.networkequipment', verbose_name='Оборудование')),
                ('subnet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='network.subnet', verbose_name='Подсеть')),
            ],
            options={
                'verbose_name': 'IP-адрес',
                'verbose_name_plural': 'IP-адреса',
                'db_table': 'network_ipaddress',
                'ordering': ['address'],
            },
        ),
    ]