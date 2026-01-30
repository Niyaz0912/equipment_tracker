# quick_snmp_test.py
from pysnmp.hlapi import *

def quick_test():
    """Быстрая проверка шлюзов"""
    gateways = [
        '192.168.8.1',    # Network device & server
        '192.168.8.65',   # Servers (.65 - необычный шлюз, но попробуем)
        '192.168.9.1',    # Kavleger
        '192.168.10.1',   # Corp network
        '192.168.11.1',   # Corp network (вторая часть /23)
        '192.168.12.1',   # DJns crankos
    ]
    
    print("⚡ Проверка шлюзов по SNMP:")
    print("=" * 40)
    
    for gw in gateways:
        print(f"\n{gw}...", end=' ')
        
        # Пробуем получить описание устройства
        try:
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData('public', mpModel=1),
                       UdpTransportTarget((gw, 161), timeout=2, retries=1),
                       ContextData(),
                       ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))
            )
            
            if errorIndication or errorStatus:
                print("❌ Нет ответа")
            else:
                description = str(varBinds[0][1])
                print(f"✅ Отвечает!")
                print(f"   Описание: {description[:60]}...")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    quick_test()