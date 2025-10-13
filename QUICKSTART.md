# Быстрый старт

## 1. Установка зависимостей

```bash
# Установите пакеты
pip install -r requirements.txt

# Или через pip install
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0 python-dotenv>=1.0.0 fastapi>=0.104.0 uvicorn[standard]>=0.24.0
```

## 2. Установка драйвера АТОЛ

Скачайте и установите драйвер АТОЛ ККТ v.10:
- Сайт: https://fs.atol.ru/
- Выберите версию для вашей ОС (Windows/Linux/macOS)

После установки драйвер будет доступен через `libfptr10`

## 3. Настройка

Создайте файл `.env` из примера:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```bash
# Путь к драйверу (если не установлен системно)
ATOL_DRIVER_PATH=

# Настройки подключения к ККТ
ATOL_CONNECTION_TYPE=tcp
ATOL_HOST=192.168.1.100
ATOL_PORT=5555

# Данные компании
COMPANY_INN=1234567890
CASHIER_NAME=Иванов И.И.

# API сервер
API_HOST=0.0.0.0
API_PORT=8000
```

## 4. Запуск сервера

```bash
# Вариант 1: через Makefile
make run-server

# Вариант 2: через uvicorn
python -m uvicorn atol_integration.api.server:app --host 0.0.0.0 --port 8000

# Вариант 3: с auto-reload для разработки
make run-server-dev
```

## 5. Проверка

Откройте в браузере:
- API документация: http://localhost:8000/docs
- Альтернативная документация: http://localhost:8000/redoc
- Проверка здоровья: http://localhost:8000/health

## 6. Первый запрос

### Проверка подключения

```bash
curl http://localhost:8000/
```

### Подключение к ККТ (если не автоподключение)

```bash
curl -X POST http://localhost:8000/connect \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "tcp",
    "host": "192.168.1.100",
    "port": 5555
  }'
```

### Получение информации о ККТ

```bash
curl http://localhost:8000/device/info
```

### Создание чека

```bash
curl -X POST http://localhost:8000/receipt/create \
  -H "Content-Type: application/json" \
  -d '{
    "receipt_type": 0,
    "cashier_name": "Иванов И.И.",
    "items": [
      {
        "name": "Тестовый товар",
        "price": 100.0,
        "quantity": 1.0,
        "tax_type": 3
      }
    ],
    "payments": [
      {
        "amount": 100.0,
        "payment_type": 0
      }
    ]
  }'
```

## Типы данных

### receipt_type (Тип чека)
- `0` - Продажа
- `1` - Возврат продажи
- `2` - Покупка
- `3` - Возврат покупки

### tax_type (НДС)
- `0` - Без НДС
- `1` - НДС 0%
- `2` - НДС 10%
- `3` - НДС 20%
- `4` - НДС 10/110
- `5` - НДС 20/120

### payment_type (Тип оплаты)
- `0` - Наличные
- `1` - Электронные
- `2` - Предоплата (аванс)
- `3` - Последующая оплата (кредит)
- `4` - Иная форма оплаты

## Troubleshooting

### Ошибка: libfptr10 не найдена

**Решение**: Установите драйвер АТОЛ или укажите путь в `.env`:
```bash
ATOL_DRIVER_PATH=/usr/local/lib/python3.10/site-packages
```

### Ошибка: драйвер не инициализирован

**Решение**: Проверьте что драйвер установлен:
```bash
python3 -c "from libfptr10 import IFptr; print('OK')"
```

### Ошибка: нет подключения к ККТ

**Решение**: 
1. Проверьте IP и порт в `.env`
2. Проверьте сетевое подключение: `ping 192.168.1.100`
3. Проверьте порт: `telnet 192.168.1.100 5555`
4. Подключитесь вручную через API: `POST /connect`

### Ошибка: смена не открыта

**Решение**: Откройте смену:
```bash
curl -X POST http://localhost:8000/shift/open \
  -H "Content-Type: application/json" \
  -d '{"cashier_name": "Иванов И.И."}'
```

## Дополнительная документация

- Полная документация API: [REST_API.md](REST_API.md)
- Справочник API: [API_REFERENCE.md](API_REFERENCE.md)
- Установка драйвера: [INSTALLATION.md](INSTALLATION.md)
- README: [README.md](README.md)

## Примеры кода

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Создать чек
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

print(response.json())
```

### JavaScript

```javascript
const response = await fetch("http://localhost:8000/receipt/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        receipt_type: 0,
        cashier_name: "Иванов И.И.",
        items: [
            {name: "Товар", price: 100.0, quantity: 1.0, tax_type: 3}
        ],
        payments: [
            {amount: 100.0, payment_type: 0}
        ]
    })
});

const result = await response.json();
console.log(result);
```

## Готово!

Теперь вы можете использовать REST API для работы с АТОЛ ККТ!
