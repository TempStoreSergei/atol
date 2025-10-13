# АТОЛ Integration

Python библиотека для интеграции с кассовым оборудованием АТОЛ через драйвер ККТ v.10.

## Возможности

### REST API (FastAPI)
- **HTTP REST API** для удаленного управления ККТ
- Автоматическая документация (Swagger/ReDoc)
- Асинхронная обработка запросов
- Автоподключение к ККТ при старте

### Драйвер ККТ
- Работа с АТОЛ ККТ через драйвер v.10 (libfptr10)
- Подключение по TCP/IP, USB, Serial (COM-порт), Bluetooth
- Полная поддержка фискальных операций
- Создание и фискализация чеков (продажа, возврат, покупка)
- Чеки коррекции (самостоятельные и по предписанию)
- Управление сменами (открытие, закрытие, статус)
- Денежные операции (внесение/выплата)
- Получение информации об устройстве и статусе
- Печать отчетов (X-отчет, Z-отчет)
- Работа с денежным ящиком

## Поддерживаемые модели

- АТОЛ 42ФС
- АТОЛ 30Ф
- АТОЛ 50Ф, 55Ф, 60Ф
- АТОЛ 90Ф, 91Ф, 92Ф

## Установка

### 1. Установка драйвера АТОЛ ККТ

Сначала необходимо установить драйвер АТОЛ ККТ v.10:

- Скачайте с официального сайта: https://fs.atol.ru/
- Установите драйвер для вашей ОС (Windows, Linux, macOS)
- Документация: https://integration.atol.ru/api/

### 2. Установка библиотеки

```bash
# Клонирование репозитория
git clone <repository_url>
cd atol_integration

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Или установка в режиме разработки
pip install -e .
```

## Быстрый старт

### Вариант 1: REST API (рекомендуется)

#### Запуск сервера

```bash
# Настройте .env файл
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Запустите сервер
python -m uvicorn atol_integration.api.server:app --host 0.0.0.0 --port 8000

# Или с auto-reload для разработки
python -m uvicorn atol_integration.api.server:app --reload
```

Сервер будет доступен по адресу:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Использование API

```bash
# Создать чек через API
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "items": [
      {"name": "Товар", "price": 100.0, "quantity": 1.0, "tax_type": 3}
    ],
    "payments": [
      {"amount": 100.0, "payment_type": 0}
    ]
  }'
```

Полная документация API: [REST_API.md](REST_API.md)

### Вариант 2: Прямое использование драйвера

#### Базовый пример продажи

```python
from atol_integration.api.driver import (
    AtolDriver,
    ConnectionType,
    ReceiptType,
    PaymentType,
    TaxType
)

# Создаем драйвер
driver = AtolDriver()

# Подключаемся к ККТ по TCP/IP
driver.connect(
    connection_type=ConnectionType.TCP,
    host="192.168.1.100",  # IP адрес ККТ
    port=5555
)

# Получаем информацию об устройстве
info = driver.get_device_info()
print(f"Модель: {info['model']}")
print(f"Серийный номер: {info['serial_number']}")

# Открываем смену (если закрыта)
shift_status = driver.get_shift_status()
if not shift_status['opened']:
    driver.open_shift(cashier_name="Иванов И.И.")

# Открываем чек продажи
driver.open_receipt(
    receipt_type=ReceiptType.SELL,
    cashier_name="Иванов И.И.",
    email="customer@example.com"
)

# Добавляем товары
driver.add_item(
    name="Молоко 3.2%",
    price=85.50,
    quantity=2.0,
    tax_type=TaxType.VAT10
)

driver.add_item(
    name="Хлеб белый",
    price=45.00,
    quantity=1.0,
    tax_type=TaxType.VAT10
)

# Добавляем оплату
total = 85.50 * 2 + 45.00
driver.add_payment(total, PaymentType.CASH)

# Закрываем чек
result = driver.close_receipt()
print(f"Чек пробит! ФД: {result['fiscal_document_number']}")

# Отключаемся
driver.disconnect()
```

### Использование контекстного менеджера

```python
with AtolDriver() as driver:
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

    driver.open_receipt(ReceiptType.SELL, "Кассир")
    driver.add_item("Товар", 100.0, 1.0, TaxType.VAT20)
    driver.add_payment(100.0, PaymentType.CASH)
    result = driver.close_receipt()

    print(f"Готово! ФД: {result['fiscal_document_number']}")
```

## Структура проекта

```
atol_integration/
├── atol_integration/      # Основной пакет
│   ├── api/              # API клиенты
│   ├── models/           # Модели данных
│   ├── services/         # Бизнес-логика
│   ├── utils/            # Утилиты
│   └── config/           # Конфигурация
├── tests/                # Тесты
│   ├── unit/            # Юнит-тесты
│   └── integration/      # Интеграционные тесты
├── examples/             # Примеры использования
├── docs/                 # Документация
├── logs/                 # Логи
└── data/                 # Данные
    ├── cache/           # Кэш
    ├── receipts/        # Чеки
    └── reports/         # Отчеты
```

## Дополнительные возможности

### Чек возврата

```python
driver.open_receipt(ReceiptType.SELL_RETURN, "Кассир")
driver.add_item("Товар", 100.0, 1.0, TaxType.VAT20)
driver.add_payment(100.0, PaymentType.CASH)
driver.close_receipt()
```

### Смешанная оплата

```python
driver.open_receipt(ReceiptType.SELL, "Кассир")
driver.add_item("Ноутбук", 45000.0, 1.0, TaxType.VAT20)

# Частично наличными, частично картой
driver.add_payment(10000.0, PaymentType.CASH)
driver.add_payment(35000.0, PaymentType.ELECTRONICALLY)

driver.close_receipt()
```

### Чек коррекции

```python
from datetime import datetime

driver.open_correction_receipt(
    correction_type=0,  # Самостоятельная
    base_date=datetime.now().strftime("%d.%m.%Y"),
    base_number="КР-001",
    base_name="Акт о возврате",
    cashier_name="Кассир"
)

driver.add_correction_item(1000.0, TaxType.VAT20, "Коррекция продажи")
driver.add_payment(1000.0, PaymentType.CASH)
driver.close_receipt()
```

### Денежные операции

```python
# Внесение денег
driver.cash_income(5000.0)

# Выплата денег
driver.cash_outcome(2000.0)
```

### Управление сменой

```python
# Открыть смену
driver.open_shift("Кассир")

# X-отчет (без гашения)
driver.x_report()

# Закрыть смену (Z-отчет)
driver.close_shift("Кассир")
```

### Типы подключения

```python
# TCP/IP
driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

# USB
driver.connect(ConnectionType.USB)

# COM-порт
driver.connect(ConnectionType.SERIAL, serial_port="COM3", baudrate=115200)

# Bluetooth
driver.connect(ConnectionType.BLUETOOTH)
```

## Тестирование

```bash
# Запуск всех тестов
make test
# или
pytest tests/ -v

# С покрытием
make test-cov
# или
pytest --cov=atol_integration --cov-report=html

# Только юнит-тесты
pytest tests/unit/

# Только интеграционные тесты
pytest tests/integration/
```

## Разработка

```bash
# Форматирование кода
make format
# или
black atol_integration/ tests/ examples/

# Проверка стиля
make lint
# или
flake8 atol_integration/ tests/ examples/
mypy atol_integration/

# Очистка
make clean

# Запуск примера
make run-example
# или
python examples/driver_basic_usage.py
```

## Документация

- Драйвер АТОЛ ККТ v.10: https://integration.atol.ru/api/
- Скачать драйвер: https://fs.atol.ru/
- Официальный сайт: https://atol.ru/

## Лицензия

MIT
