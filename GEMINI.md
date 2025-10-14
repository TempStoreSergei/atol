# Улучшенная обработка ошибок - Реализовано

## Обзор изменений

В ответ на запрос пользователя о более детальной информации об ошибках, была реализована расширенная система обработки ошибок драйвера АТОЛ.

### До изменений

Ошибки возвращались только с кратким описанием:
```json
{
  "detail": "Ошибка промотки ленты: Механическая ошибка печатающего устройства"
}
```

### После изменений

Теперь ошибки содержат полную диагностическую информацию:
```json
{
  "error": "AtolDriverError",
  "detail": "[Код 15] Механическая ошибка печатающего устройства: детальное описание",
  "error_code": 15,
  "error_description": "Механическая ошибка печатающего устройства: детальное описание",
  "message": "Ошибка промотки ленты",
  "docs_url": "https://integration.atol.ru/api/#!error-15"
}
```

## Реализованные компоненты

### 1. Класс `AtolDriverError` (driver.py:50-78)

Базовый класс исключения для ошибок драйвера АТОЛ с расширенными атрибутами:

```python
class AtolDriverError(Exception):
    """Базовое исключение для ошибок драйвера АТОЛ"""

    def __init__(self, message: str, error_code: Optional[int] = None,
                 error_description: Optional[str] = None):
        """
        Инициализация ошибки

        Args:
            message: Сообщение об ошибке (контекст операции)
            error_code: Код ошибки из драйвера (0-603)
            error_description: Детальное описание ошибки из драйвера
        """
        super().__init__(message)
        self.error_code = error_code
        self.error_description = error_description or message
        self.message = message

    def __str__(self):
        """Форматированное строковое представление"""
        if self.error_code is not None:
            return f"[Код {self.error_code}] {self.error_description}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для API"""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "error_description": self.error_description
        }
```

**Возможности:**
- Хранит три типа информации: message (контекст), error_code (код), error_description (детали)
- Форматированный вывод с кодом ошибки: `[Код 15] Описание`
- Метод `to_dict()` для API-ответов
- Совместимость с существующим кодом (опциональные параметры)

### 2. Метод `_check_result()` (driver.py:180-194)

Улучшенная проверка результата операций драйвера:

```python
def _check_result(self, result: int, operation: str = "") -> None:
    """Проверить результат операции"""
    if result < 0:
        # Получаем код ошибки из драйвера
        error_code = self.fptr.errorCode()

        # Получаем описание ошибки из драйвера
        error_desc = self.fptr.errorDescription()

        # Импортируем функцию получения русского описания ошибки
        from .errors import get_error_message
        error_message_ru = get_error_message(error_code)

        # Выбрасываем исключение с полной информацией
        raise AtolDriverError(
            message=f"Ошибка {operation}" if operation else "Ошибка операции",
            error_code=error_code,
            error_description=f"{error_message_ru}: {error_desc}"
        )
```

**Функционал:**
- Автоматически получает `error_code` через `fptr.errorCode()`
- Автоматически получает `error_description` через `fptr.errorDescription()`
- Добавляет русское описание ошибки из словаря `ERROR_MESSAGES`
- Создает исключение с полным контекстом операции

### 3. Обработчик ошибок FastAPI (server.py:322-342)

Глобальный обработчик исключений для API:

```python
@app.exception_handler(AtolDriverError)
async def atol_driver_error_handler(request, exc: AtolDriverError):
    """Обработчик ошибок драйвера с подробной информацией"""
    error_content = {
        "error": "AtolDriverError",
        "detail": str(exc),
    }

    # Добавляем код ошибки и описание если доступны
    if hasattr(exc, 'error_code') and exc.error_code is not None:
        error_content["error_code"] = exc.error_code
        error_content["error_description"] = exc.error_description
        error_content["message"] = exc.message

        # Добавляем ссылку на документацию по ошибке
        error_content["docs_url"] = f"https://integration.atol.ru/api/#!error-{exc.error_code}"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_content
    )
```

**Возможности:**
- Перехватывает все исключения `AtolDriverError`
- Формирует структурированный JSON-ответ
- Добавляет ссылку на документацию АТОЛ для каждого кода ошибки
- HTTP статус 400 (Bad Request) для ошибок драйвера

### 4. Полный словарь ошибок (errors.py)

Все 269 кодов ошибок (000-603) с русскими описаниями:

```python
ERROR_MESSAGES.update({
    # Успех
    DriverErrorCode.OK: "Ошибок нет",

    # Ошибки подключения (1-15)
    DriverErrorCode.CONNECTION_DISABLED: "Соединение не установлено",
    DriverErrorCode.NO_CONNECTION: "Нет связи",
    DriverErrorCode.WRONG_PASSWORD: "Неверный пароль",
    DriverErrorCode.DEVICE_NOT_FOUND: "Устройство не найдено",
    DriverErrorCode.INVALID_PORT_NAME: "Некорректное имя порта",
    DriverErrorCode.PORT_BUSY: "Порт занят",
    # ... всего 269 кодов

    # Ошибки удалённого подключения (601-603)
    DriverErrorCode.RCP_SERVER_BUSY: "Устройство занято другим клиентом",
    DriverErrorCode.RCP_SERVER_VERSION: "Некорректная версия протокола",
    DriverErrorCode.RCP_SERVER_EXCHANGE: "Ошибка обмена с сервером",
})
```

## Примеры использования

### Пример 1: Ошибка с кодом

**Запрос:**
```bash
curl -X POST http://localhost:8000/print/feed -H "Content-Type: application/json" -d '{"lines": 100}'
```

**Ответ при ошибке:**
```json
{
  "error": "AtolDriverError",
  "detail": "[Код 15] Механическая ошибка печатающего устройства: нет бумаги или замятие",
  "error_code": 15,
  "error_description": "Механическая ошибка печатающего устройства: нет бумаги или замятие",
  "message": "Ошибка промотки ленты",
  "docs_url": "https://integration.atol.ru/api/#!error-15"
}
```

### Пример 2: Ошибка подключения

**Запрос:**
```bash
curl -X POST http://localhost:8000/connection/open -H "Content-Type: application/json" \
  -d '{"connection_type": "tcp", "host": "192.168.1.100", "port": 5555}'
```

**Ответ при ошибке:**
```json
{
  "error": "AtolDriverError",
  "detail": "[Код 2] Нет связи: таймаут подключения",
  "error_code": 2,
  "error_description": "Нет связи: таймаут подключения",
  "message": "Ошибка открытия соединения",
  "docs_url": "https://integration.atol.ru/api/#!error-2"
}
```

### Пример 3: Ошибка операции с чеком

**Запрос:**
```bash
curl -X POST http://localhost:8000/receipt/close
```

**Ответ при ошибке:**
```json
{
  "error": "AtolDriverError",
  "detail": "[Код 42] Чек не открыт: невозможно закрыть несуществующий чек",
  "error_code": 42,
  "error_description": "Чек не открыт: невозможно закрыть несуществующий чек",
  "message": "Ошибка закрытия чека",
  "docs_url": "https://integration.atol.ru/api/#!error-42"
}
```

## Преимущества новой системы

### 1. Диагностика проблем
- **Код ошибки** позволяет точно идентифицировать тип проблемы
- **Детальное описание** объясняет причину ошибки
- **Контекст операции** показывает, что пыталось сделать приложение
- **Ссылка на документацию** для быстрого поиска решения

### 2. Совместимость
- Обратная совместимость с существующим кодом
- Опциональные параметры в `AtolDriverError`
- Работает со всеми существующими endpoint'ами

### 3. Автоматизация
- Все ошибки драйвера автоматически обогащаются информацией
- Не требует изменений в endpoint'ах
- Централизованная обработка в `_check_result()`

### 4. Интеграция
- Готовые JSON-ответы для клиентов
- Структурированный формат для логирования
- Ссылки на документацию АТОЛ

## Коды наиболее частых ошибок

| Код | Название | Описание | Решение |
|-----|----------|----------|---------|
| 0 | OK | Ошибок нет | - |
| 1 | CONNECTION_DISABLED | Соединение не установлено | Вызвать `/connection/open` |
| 2 | NO_CONNECTION | Нет связи | Проверить подключение, IP, порт |
| 15 | MECHANICAL_ERROR | Механическая ошибка печатающего устройства | Проверить бумагу, крышку |
| 42 | RECEIPT_NOT_OPENED | Чек не открыт | Вызвать `/receipt/open` |
| 43 | SHIFT_NOT_OPENED | Смена не открыта | Вызвать `/shift/open` |
| 51 | FN_DATA_WAITING | Ожидание данных от ФН | Дождаться завершения |
| 239 | SHIFT_EXPIRED | Смена более 24 часов | Закрыть и открыть новую смену |
| 377 | DOCUMENTS_QUEUE_OVERFLOW | Очередь ОФД переполнена | Проверить соединение с ОФД |
| 601 | RCP_SERVER_BUSY | Устройство занято другим клиентом | Дождаться освобождения |

## Endpoint для получения информации об ошибках

### GET `/driver/error`
Получить последнюю ошибку драйвера:

```bash
curl http://localhost:8000/driver/error
```

Ответ:
```json
{
  "error_code": 15,
  "error_description": "Механическая ошибка печатающего устройства",
  "error_name": "Механическая ошибка печатающего устройства"
}
```

### POST `/driver/error/reset`
Сбросить информацию о последней ошибке:

```bash
curl -X POST http://localhost:8000/driver/error/reset
```

### GET `/driver/errors/codes`
Получить полный справочник кодов ошибок (269 кодов):

```bash
curl http://localhost:8000/driver/errors/codes
```

Ответ (сокращенно):
```json
{
  "error_codes": [
    {
      "code": 0,
      "name": "OK",
      "message": "Ошибок нет"
    },
    {
      "code": 1,
      "name": "CONNECTION_DISABLED",
      "message": "Соединение не установлено"
    },
    ...
  ]
}
```

## Тестирование

Протестировано:
- ✓ Создание исключений с кодом и без
- ✓ Форматирование строкового представления
- ✓ Метод `to_dict()` для API
- ✓ Формирование JSON-ответов с полной информацией
- ✓ Ссылки на документацию
- ✓ Обратная совместимость

## Дополнительные возможности

### Логирование ошибок

Все ошибки автоматически логируются в `driver.py`:

```python
logger.error(f"Ошибка {operation}: {e}")  # Записывается в лог
```

Формат лога:
```
2025-10-14 10:30:45 ERROR Ошибка закрытия чека: [Код 42] Чек не открыт
```

### CUPS Integration

Пользователь упомянул, что принтер работает через CUPS (localhost:631) после установки драйверов. Это означает:
- Драйвер АТОЛ установлен корректно
- CUPS может использоваться для нефискальной печати
- Прямое подключение через libfptr10 для фискальных операций

## Итого

Реализована полная система расширенной обработки ошибок:
- ✅ Класс `AtolDriverError` с тремя уровнями информации
- ✅ Автоматическое получение кодов и описаний ошибок
- ✅ Глобальный обработчик для FastAPI
- ✅ Полный словарь 269 кодов ошибок на русском
- ✅ Ссылки на документацию АТОЛ
- ✅ Endpoint'ы для диагностики
- ✅ Обратная совместимость

Теперь API возвращает полную диагностическую информацию для каждой ошибки драйвера АТОЛ.
