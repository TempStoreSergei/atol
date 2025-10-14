# REST API Документация

Полная документация REST API для работы с АТОЛ ККТ.

## Запуск сервера

```bash
# Запуск сервера
python -m uvicorn atol_integration.api.server:app --host 0.0.0.0 --port 8000

# Или с auto-reload для разработки
python -m uvicorn atol_integration.api.server:app --reload

# Или через python
python -m atol_integration.api.server
```

После запуска:
- API доступно по адресу: http://localhost:8000
- Интерактивная документация (Swagger): http://localhost:8000/docs
- Альтернативная документация (ReDoc): http://localhost:8000/redoc

## Базовые эндпоинты

### GET /

Проверка статуса API

```bash
curl http://localhost:8000/
```

Ответ:
```json
{
  "name": "АТОЛ ККТ API",
  "version": "0.2.0",
  "status": "running",
  "connected": true
}
```

### GET /health

Проверка здоровья сервиса

```bash
curl http://localhost:8000/health
```

## Подключение к ККТ

### POST /connect

Подключиться к ККТ

```bash
# TCP/IP
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "tcp",
    "host": "192.168.1.100",
    "port": 5555
  }'

# USB
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "usb"}'

# Serial (COM-порт)
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "serial",
    "serial_port": "COM3",
    "baudrate": 115200
  }'
```

### POST /disconnect

Отключиться от ККТ

```bash
curl -X POST http://localhost:8000/disconnect
```

### GET /status

Получить статус подключения

```bash
curl http://localhost:8000/status
```

## Информация об устройстве

### GET /device/info

Получить информацию об устройстве

```bash
curl http://localhost:8000/device/info
```

Ответ:
```json
{
  "model": "АТОЛ 42ФС",
  "serial_number": "12345678",
  "firmware_version": "10.8.0.0",
  "fiscal_mode": true,
  "fn_serial": "9999078900001234",
  "fn_fiscal_sign": "123456789",
  "inn": "1234567890",
  "reg_number": "0001234567891234"
}
```

### GET /shift/status

Получить статус смены

```bash
curl http://localhost:8000/shift/status
```

Ответ:
```json
{
  "opened": true,
  "number": 42,
  "receipt_count": 15
}
```

## Управление сменой

### POST /shift/open

Открыть смену

```bash
curl -X POST http://localhost:8000/shift/open \
  -H "Content-Type: application/json" \
  -d '{
    "cashier_name": "Иванов И.И."
  }'
```

### POST /shift/close

Закрыть смену (Z-отчет)

```bash
curl -X POST http://localhost:8000/shift/close \
  -H "Content-Type: application/json" \
  -d '{
    "cashier_name": "Иванов И.И."
  }'
```

### POST /shift/x-report

Напечатать X-отчет (без гашения)

```bash
curl -X POST http://localhost:8000/shift/x-report
```

## Операции с чеками

### Пошаговое создание чека

#### POST /receipt/open

Открыть чек

```bash
curl -X POST http://localhost:8000/receipt/open \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "email": "customer@example.com"
  }'
```

Типы чеков (receipt_type):
- `0` - Продажа
- `1` - Возврат продажи
- `2` - Покупка
- `3` - Возврат покупки

#### POST /receipt/add-item

Добавить товар

```bash
curl -X POST http://localhost:8000/receipt/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Молоко 3.2%",
    "price": 85.50,
    "quantity": 2.0,
    "tax_type": 2,
    "measure_unit": "шт"
  }'
```

Типы НДС (tax_type):
- `0` - Без НДС
- `1` - НДС 0%
- `2` - НДС 10%
- `3` - НДС 20%
- `4` - НДС 10/110
- `5` - НДС 20/120

#### POST /receipt/add-payment

Добавить оплату

```bash
curl -X POST http://localhost:8000/receipt/add-payment \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 171.0,
    "payment_type": 0
  }'
```

Типы оплаты (payment_type):
- `0` - Наличные
- `1` - Электронные
- `2` - Предоплата (аванс)
- `3` - Последующая оплата (кредит)
- `4` - Иная форма

#### POST /receipt/close

Закрыть и напечатать чек

```bash
curl -X POST http://localhost:8000/receipt/close
```

Ответ:
```json
{
  "success": true,
  "fiscal_document_number": 42,
  "fiscal_sign": 123456789,
  "shift_number": 15,
  "receipt_number": 42,
  "datetime": "2024-01-15 14:30:00"
}
```

#### POST /receipt/cancel

Отменить текущий чек

```bash
curl -X POST http://localhost:8000/receipt/cancel
```

### Создание чека одним запросом

#### POST /receipt/create

Создать и закрыть чек одним запросом

```bash
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "email": "customer@example.com",
    "items": [
      {
        "name": "Молоко 3.2%",
        "price": 85.50,
        "quantity": 2.0,
        "tax_type": 2
      },
      {
        "name": "Хлеб белый",
        "price": 45.00,
        "quantity": 1.0,
        "tax_type": 2
      }
    ],
    "payments": [
      {
        "amount": 216.0,
        "payment_type": 0
      }
    ]
  }'
```

## Чеки коррекции

### POST /correction/open

Открыть чек коррекции

```bash
curl -X POST http://localhost:8000/correction/open \
  -H "Content-Type: application/json" \
  -d '{
    "correction_type": 0,
    "base_date": "15.01.2024",
    "base_number": "КР-001",
    "base_name": "Акт о возврате денежных средств",
    "cashier_name": "Иванов И.И."
  }'
```

### POST /correction/add-item

Добавить позицию в чек коррекции

```bash
curl -X POST http://localhost:8000/correction/add-item \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.0,
    "tax_type": 3,
    "description": "Коррекция продажи от 01.01.2024"
  }'
```

## Денежные операции

### POST /cash/income

Внести наличные

```bash
curl -X POST http://localhost:8000/cash/income \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000.0
  }'
```

### POST /cash/outcome

Выплатить наличные

```bash
curl -X POST http://localhost:8000/cash/outcome \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2000.0
  }'
```

## Вспомогательные функции

### POST /device/beep

Издать звуковой сигнал

```bash
curl -X POST http://localhost:8000/device/beep
```

### POST /device/open-drawer

Открыть денежный ящик

```bash
curl -X POST http://localhost:8000/device/open-drawer
```

### POST /device/cut-paper

Отрезать чек

```bash
curl -X POST http://localhost:8000/device/cut-paper
```

## Примеры использования

### Полный процесс продажи

```bash
# 1. Подключиться к ККТ
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "tcp", "host": "192.168.1.100", "port": 5555}'

# 2. Проверить/открыть смену
curl http://localhost:8000/shift/status
curl -X POST http://localhost:8000/shift/open \
  -H "Content-Type: application/json" \
  -d '{"cashier_name": "Иванов И.И."}'

# 3. Создать чек одним запросом
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "items": [
      {"name": "Товар 1", "price": 100.0, "quantity": 2.0, "tax_type": 3},
      {"name": "Товар 2", "price": 50.0, "quantity": 1.0, "tax_type": 2}
    ],
    "payments": [
      {"amount": 250.0, "payment_type": 0}
    ]
  }'

# 4. Подать сигнал
curl -X POST http://localhost:8000/device/beep
```

### Возврат товара

```bash
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 1,
    "cashier_name": "Иванов И.И.",
    "email": "customer@example.com",
    "items": [
      {"name": "Товар для возврата", "price": 100.0, "quantity": 1.0, "tax_type": 3}
    ],
    "payments": [
      {"amount": 100.0, "payment_type": 0}
    ]
  }'
```

### Смешанная оплата (наличные + карта)

```bash
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "items": [
      {"name": "Товар", "price": 1000.0, "quantity": 1.0, "tax_type": 3}
    ],
    "payments": [
      {"amount": 300.0, "payment_type": 0},
      {"amount": 700.0, "payment_type": 1}
    ]
  }'
```

## Обработка ошибок

Все ошибки возвращаются в формате:

```json
{
  "error": "AtolDriverError",
  "detail": "Описание ошибки"
}
```

HTTP коды:
- `200` - Успешно
- `400` - Ошибка запроса или драйвера
- `503` - Сервис недоступен (драйвер не инициализирован или нет подключения)

## Python клиент

Пример использования API из Python:

```python
import requests

BASE_URL = "http://localhost:8000"

# Подключение
response = requests.post(f"{BASE_URL}/connect", json={
    "connection_type": "tcp",
    "host": "192.168.1.100",
    "port": 5555
})
print(response.json())

# Информация об устройстве
response = requests.get(f"{BASE_URL}/device/info")
device_info = response.json()
print(f"Модель: {device_info['model']}")

# Создание чека
response = requests.post(f"{BASE_URL}/receipt/create", json={
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "items": [
        {"name": "Товар", "price": 100.0, "quantity": 1.0, "tax_type": 3}
    ],
    "payments": [
        {"amount": 100.0, "payment_type": 0}
    ]
})

if response.status_code == 200:
    result = response.json()
    print(f"Чек пробит! ФД: {result['fiscal_document_number']}")
else:
    print(f"Ошибка: {response.json()}")
```

## JavaScript/Node.js клиент

```javascript
const BASE_URL = "http://localhost:8000";

// Создание чека
async function createReceipt() {
    const response = await fetch(`${BASE_URL}/receipt/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            receipt_type: 0,
            cashier_name: "Иванов И.И.",
            items: [
                { name: "Товар", price: 100.0, quantity: 1.0, tax_type: 3 }
            ],
            payments: [
                { amount: 100.0, payment_type: 0 }
            ]
        })
    });

    const result = await response.json();
    console.log(result);
}

createReceipt();
```
