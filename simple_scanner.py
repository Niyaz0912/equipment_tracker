# simple_scanner.py - положи в корень проекта
import sys
import json

# Импортируем твой скрипт
from network_scanner import simple_network_scan

if __name__ == "__main__":
    if '--json' in sys.argv:
        devices, _ = simple_network_scan()
        print(json.dumps(devices, ensure_ascii=False))
    else:
        simple_network_scan()