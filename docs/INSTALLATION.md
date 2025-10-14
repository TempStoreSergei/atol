# Установка и настройка

Подробная инструкция по установке драйвера АТОЛ и библиотеки.

## 1. Установка драйвера АТОЛ ККТ v.10

### Windows

1. Скачайте драйвер с официального сайта: https://fs.atol.ru/
2. Запустите установщик `DriverATOL_v10.x.x.x_setup.exe`
3. Следуйте инструкциям мастера установки
4. После установки драйвер будет доступен в системе

### Linux

1. Скачайте пакет для вашего дистрибутива:
   - Debian/Ubuntu: `.deb` пакет
   - RedHat/CentOS: `.rpm` пакет
   - Или универсальный архив `.tar.gz`

2. Установите пакет:
   ```bash
   # Debian/Ubuntu
   sudo dpkg -i libfptr10_10.x.x.x_amd64.deb
   sudo apt-get install -f  # установить зависимости

   # RedHat/CentOS
   sudo rpm -i libfptr10-10.x.x.x-1.x86_64.rpm

   # Или из архива
   tar -xzf libfptr10_10.x.x.x_linux_x86_64.tar.gz
   cd libfptr10
   sudo ./install.sh
   ```

3. Проверьте установку:
   ```bash
   python3 -c "from libfptr10 import IFptr; print('Driver installed')"
   ```

### macOS

1. Скачайте установщик для macOS с https://fs.atol.ru/
2. Откройте `.dmg` файл
3. Перетащите приложение в папку Applications
4. Запустите установщик и следуйте инструкциям

## 2. Установка библиотеки atol_integration

### Из исходников

```bash
# Клонируйте репозиторий
git clone <repository_url>
cd atol_integration

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Установите библиотеку в режиме разработки
pip install -e .
```

### Из PyPI (когда будет опубликовано)

```bash
pip install atol-integration
```

## 3. Настройка подключения к ККТ

### TCP/IP подключение (рекомендуется)

1. Узнайте IP-адрес вашей ККТ (например, `192.168.1.100`)
2. Убедитесь что ККТ настроена на работу через TCP/IP
3. Порт по умолчанию: `5555`

Пример кода:
```python
from atol_integration.api.driver import AtolDriver, ConnectionType

driver = AtolDriver()
driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
```

### USB подключение

1. Подключите ККТ к компьютеру через USB
2. Убедитесь что драйвер распознал устройство

Пример кода:
```python
driver.connect(ConnectionType.USB)
```

### COM-порт (Serial)

1. Подключите ККТ к COM-порту
2. Узнайте номер порта (Windows: `COM3`, Linux: `/dev/ttyS0`)

Пример кода:
```python
driver.connect(ConnectionType.SERIAL, serial_port="COM3", baudrate=115200)
# или на Linux
driver.connect(ConnectionType.SERIAL, serial_port="/dev/ttyS0", baudrate=115200)
```

## 4. Проверка установки

Запустите тестовый скрипт:

```python
from atol_integration.api.driver import AtolDriver, ConnectionType

# Создаем драйвер
driver = AtolDriver()

try:
    # Подключаемся (замените на ваш IP)
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
    print("✓ Подключение успешно")

    # Получаем информацию об устройстве
    info = driver.get_device_info()
    print(f"✓ Модель: {info['model']}")
    print(f"✓ Серийный номер: {info['serial_number']}")
    print(f"✓ Версия ПО: {info['firmware_version']}")
    print(f"✓ ИНН: {info['inn']}")

    # Проверяем статус смены
    shift = driver.get_shift_status()
    print(f"✓ Смена открыта: {shift['opened']}")

    print("\n✓ Всё работает!")

except Exception as e:
    print(f"✗ Ошибка: {e}")

finally:
    driver.disconnect()
```

## 5. Устранение проблем

### Ошибка: libfptr10 не найдена

**Причина:** Драйвер АТОЛ не установлен или установлен неправильно

**Решение:**
1. Переустановите драйвер АТОЛ ККТ v.10
2. Убедитесь что Python может найти библиотеку:
   ```bash
   python3 -c "import sys; print(sys.path)"
   python3 -c "from libfptr10 import IFptr"
   ```

### Ошибка подключения к ККТ

**Причина:** Неверный IP, порт или ККТ выключена

**Решение:**
1. Проверьте что ККТ включена и подключена к сети
2. Проверьте IP-адрес (пинг):
   ```bash
   ping 192.168.1.100
   ```
3. Убедитесь что порт открыт (telnet):
   ```bash
   telnet 192.168.1.100 5555
   ```
4. Проверьте настройки сетевого интерфейса ККТ

### Ошибка: смена не открыта

**Причина:** Смена закрыта, нужно открыть

**Решение:**
```python
shift_status = driver.get_shift_status()
if not shift_status['opened']:
    driver.open_shift(cashier_name="Кассир")
```

### Ошибка фискализации

**Причина:** Проблемы с фискальным накопителем или настройками

**Решение:**
1. Проверьте срок действия ФН (фискального накопителя)
2. Убедитесь что ККТ зарегистрирована в ФНС
3. Проверьте интернет-соединение (для передачи в ОФД)
4. Проверьте настройки ОФД в ККТ

## 6. Полезные ссылки

- Драйвер АТОЛ: https://fs.atol.ru/
- Документация API: https://integration.atol.ru/api/
- Техподдержка АТОЛ: https://atol.ru/support/
- 54-ФЗ (закон о ККТ): http://www.consultant.ru/document/cons_doc_LAW_42359/

## 7. Примеры использования

После успешной установки изучите примеры:

```bash
# Базовый пример
python examples/driver_basic_usage.py

# Расширенные примеры
python examples/driver_advanced_usage.py
```

Или посмотрите код в файлах:
- `examples/driver_basic_usage.py` - простая продажа
- `examples/driver_advanced_usage.py` - все возможности
