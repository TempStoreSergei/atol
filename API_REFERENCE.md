# API Reference

Справочник по API библиотеки atol_integration.

## AtolDriver

Основной класс для работы с АТОЛ ККТ через драйвер v.10.

### Инициализация и подключение

```python
from atol_integration import AtolDriver, ConnectionType

driver = AtolDriver()
```

#### `connect(connection_type, host, port, serial_port, baudrate)`

Подключиться к ККТ.

**Параметры:**
- `connection_type` (ConnectionType): Тип подключения
- `host` (str): IP адрес для TCP (по умолчанию: "localhost")
- `port` (int): Порт для TCP (по умолчанию: 5555)
- `serial_port` (str): COM порт для Serial
- `baudrate` (int): Скорость для Serial (по умолчанию: 115200)

**Возвращает:** `bool` - успех подключения

**Пример:**
```python
# TCP/IP
driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

# USB
driver.connect(ConnectionType.USB)

# Serial
driver.connect(ConnectionType.SERIAL, serial_port="COM3")
```

#### `disconnect()`

Отключиться от ККТ.

#### `is_connected()`

Проверить статус подключения.

**Возвращает:** `bool`

---

### Информация об устройстве

#### `get_device_info()`

Получить информацию об устройстве.

**Возвращает:** `Dict[str, Any]`
```python
{
    "model": "АТОЛ 42ФС",
    "serial_number": "12345678",
    "firmware_version": "10.8.0.0",
    "fiscal_mode": True,
    "fn_serial": "9999078900001234",
    "fn_fiscal_sign": "123456789",
    "inn": "1234567890",
    "reg_number": "0001234567891234"
}
```

#### `get_shift_status()`

Получить статус смены.

**Возвращает:** `Dict[str, Any]`
```python
{
    "opened": True,
    "number": 42,
    "receipt_count": 15
}
```

---

### Управление сменой

#### `open_shift(cashier_name)`

Открыть смену.

**Параметры:**
- `cashier_name` (str): Имя кассира (по умолчанию: "Кассир")

**Возвращает:** `Dict[str, Any]` - статус смены

**Пример:**
```python
driver.open_shift("Иванов И.И.")
```

#### `close_shift(cashier_name)`

Закрыть смену (печать Z-отчета).

**Параметры:**
- `cashier_name` (str): Имя кассира

**Возвращает:** `Dict[str, Any]`

#### `x_report()`

Напечатать X-отчет (без гашения).

**Возвращает:** `bool`

---

### Операции с чеками

#### `open_receipt(receipt_type, cashier_name, email, phone)`

Открыть чек.

**Параметры:**
- `receipt_type` (ReceiptType): Тип чека
- `cashier_name` (str): Имя кассира
- `email` (str, optional): Email покупателя
- `phone` (str, optional): Телефон покупателя

**Возвращает:** `bool`

**Пример:**
```python
driver.open_receipt(
    ReceiptType.SELL,
    "Иванов И.И.",
    email="customer@example.com"
)
```

#### `add_item(name, price, quantity, tax_type, department, measure_unit)`

Добавить товар в чек.

**Параметры:**
- `name` (str): Название товара
- `price` (float): Цена за единицу
- `quantity` (float): Количество (по умолчанию: 1.0)
- `tax_type` (TaxType): Тип НДС (по умолчанию: NONE)
- `department` (int): Номер отдела (по умолчанию: 1)
- `measure_unit` (str): Единица измерения (по умолчанию: "шт")

**Возвращает:** `bool`

**Пример:**
```python
driver.add_item(
    "Молоко 3.2%",
    price=85.50,
    quantity=2.0,
    tax_type=TaxType.VAT10,
    measure_unit="шт"
)
```

#### `add_payment(amount, payment_type)`

Добавить оплату.

**Параметры:**
- `amount` (float): Сумма оплаты
- `payment_type` (PaymentType): Тип оплаты (по умолчанию: CASH)

**Возвращает:** `bool`

**Пример:**
```python
driver.add_payment(100.0, PaymentType.CASH)
driver.add_payment(200.0, PaymentType.ELECTRONICALLY)
```

#### `close_receipt()`

Закрыть и напечатать чек.

**Возвращает:** `Dict[str, Any]`
```python
{
    "success": True,
    "fiscal_document_number": 42,
    "fiscal_sign": "123456789",
    "shift_number": 15,
    "receipt_number": 42,
    "datetime": "2024-01-15 14:30:00"
}
```

#### `cancel_receipt()`

Отменить текущий чек.

**Возвращает:** `bool`

---

### Чеки коррекции

#### `open_correction_receipt(correction_type, base_date, base_number, base_name, cashier_name)`

Открыть чек коррекции.

**Параметры:**
- `correction_type` (int): Тип коррекции (0 - самостоятельно, 1 - по предписанию)
- `base_date` (str, optional): Дата документа основания (формат DD.MM.YYYY)
- `base_number` (str, optional): Номер документа основания
- `base_name` (str, optional): Наименование документа основания
- `cashier_name` (str): Имя кассира

**Возвращает:** `bool`

**Пример:**
```python
driver.open_correction_receipt(
    correction_type=0,
    base_date="15.01.2024",
    base_number="КР-001",
    base_name="Акт о возврате денежных средств",
    cashier_name="Иванов И.И."
)
```

#### `add_correction_item(amount, tax_type, description)`

Добавить сумму в чек коррекции.

**Параметры:**
- `amount` (float): Сумма коррекции
- `tax_type` (TaxType): Тип НДС (по умолчанию: NONE)
- `description` (str): Описание (по умолчанию: "Коррекция")

**Возвращает:** `bool`

---

### Денежные операции

#### `cash_income(amount)`

Внести наличные в кассу.

**Параметры:**
- `amount` (float): Сумма для внесения

**Возвращает:** `bool`

**Пример:**
```python
driver.cash_income(5000.0)
```

#### `cash_outcome(amount)`

Выплатить наличные из кассы.

**Параметры:**
- `amount` (float): Сумма для выплаты

**Возвращает:** `bool`

**Пример:**
```python
driver.cash_outcome(2000.0)
```

---

### Вспомогательные методы

#### `beep()`

Издать звуковой сигнал.

**Возвращает:** `bool`

#### `open_cash_drawer()`

Открыть денежный ящик.

**Возвращает:** `bool`

#### `cut_paper()`

Отрезать чек.

**Возвращает:** `bool`

---

## Перечисления (Enums)

### ConnectionType

Типы подключения к ККТ:
- `USB = 0` - USB подключение
- `SERIAL = 1` - Serial (COM-порт)
- `TCP = 2` - TCP/IP
- `BLUETOOTH = 3` - Bluetooth

### ReceiptType

Типы чеков:
- `SELL = 0` - Продажа
- `SELL_RETURN = 1` - Возврат продажи
- `BUY = 2` - Покупка
- `BUY_RETURN = 3` - Возврат покупки
- `SELL_CORRECTION = 4` - Коррекция продажи
- `BUY_CORRECTION = 5` - Коррекция покупки

### PaymentType

Типы оплаты:
- `CASH = 0` - Наличные
- `ELECTRONICALLY = 1` - Электронными
- `PREPAID = 2` - Предварительная оплата (аванс)
- `CREDIT = 3` - Последующая оплата (кредит)
- `OTHER = 4` - Иная форма оплаты

### TaxType

Типы НДС:
- `NONE = 0` - Без НДС
- `VAT0 = 1` - НДС 0%
- `VAT10 = 2` - НДС 10%
- `VAT20 = 3` - НДС 20%
- `VAT110 = 4` - НДС 10/110
- `VAT120 = 5` - НДС 20/120

### PaymentMethodType

Признак способа расчета (54-ФЗ):
- `FULL_PREPAYMENT = 1` - Предоплата 100%
- `PARTIAL_PREPAYMENT = 2` - Частичная предоплата
- `ADVANCE = 3` - Аванс
- `FULL_PAYMENT = 4` - Полный расчет
- `PARTIAL_PAYMENT_CREDIT = 5` - Частичный расчет и кредит
- `CREDIT = 6` - Передача в кредит
- `CREDIT_PAYMENT = 7` - Оплата кредита

### PaymentObjectType

Признак предмета расчета (54-ФЗ):
- `COMMODITY = 1` - Товар
- `EXCISE = 2` - Подакцизный товар
- `JOB = 3` - Работа
- `SERVICE = 4` - Услуга
- `GAMBLING_BET = 5` - Ставка азартной игры
- `GAMBLING_PRIZE = 6` - Выигрыш азартной игры
- `LOTTERY = 7` - Лотерейный билет
- `LOTTERY_PRIZE = 8` - Выигрыш лотереи
- `INTELLECTUAL = 9` - Предоставление РИД
- `PAYMENT = 10` - Платеж
- `AGENT_COMMISSION = 11` - Агентское вознаграждение
- `COMPOSITE = 12` - Составной предмет расчета
- `OTHER = 13` - Иной предмет расчета

---

## Исключения

### AtolDriverError

Базовое исключение для всех ошибок драйвера.

**Пример обработки:**
```python
try:
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
    # ... операции
except AtolDriverError as e:
    print(f"Ошибка драйвера: {e}")
```

---

## Контекстный менеджер

Класс `AtolDriver` поддерживает протокол контекстного менеджера:

```python
with AtolDriver() as driver:
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)
    # ... операции
    # автоматическое отключение при выходе
```

---

## Полный пример

```python
from atol_integration import (
    AtolDriver,
    ConnectionType,
    ReceiptType,
    PaymentType,
    TaxType,
    AtolDriverError
)

try:
    # Инициализация и подключение
    driver = AtolDriver()
    driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

    # Получение информации
    info = driver.get_device_info()
    print(f"Модель: {info['model']}")

    # Открытие смены (если закрыта)
    shift = driver.get_shift_status()
    if not shift['opened']:
        driver.open_shift("Иванов И.И.")

    # Создание чека
    driver.open_receipt(ReceiptType.SELL, "Иванов И.И.")
    driver.add_item("Товар 1", 100.0, 2.0, TaxType.VAT20)
    driver.add_item("Товар 2", 50.0, 1.0, TaxType.VAT10)
    driver.add_payment(250.0, PaymentType.CASH)

    # Закрытие чека
    result = driver.close_receipt()
    print(f"Чек №{result['receipt_number']}, ФД №{result['fiscal_document_number']}")

    # Отключение
    driver.disconnect()

except AtolDriverError as e:
    print(f"Ошибка: {e}")
    # Отмена чека при ошибке
    try:
        driver.cancel_receipt()
    except:
        pass
```
