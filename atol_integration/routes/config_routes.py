"""
REST API endpoint'ы для настройки драйвера и логирования
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/config", tags=["Configuration & Logging"])


# ========== МОДЕЛИ ДАННЫХ ==========

class LoggingConfigRequest(BaseModel):
    """Настройка логирования драйвера"""
    root_level: str = Field("ERROR", description="Уровень логирования: ERROR, INFO, DEBUG")
    fiscal_printer_level: Optional[str] = Field(None, description="Уровень для FiscalPrinter (ERROR, INFO, DEBUG)")
    transport_level: Optional[str] = Field(None, description="Уровень для Transport (ERROR, INFO, DEBUG)")
    ethernet_over_transport_level: Optional[str] = Field(None, description="Уровень для EthernetOverTransport")
    device_debug_level: Optional[str] = Field(None, description="Уровень для DeviceDebug")
    usb_level: Optional[str] = Field(None, description="Уровень для USB")
    com_level: Optional[str] = Field(None, description="Уровень для COM")
    tcp_level: Optional[str] = Field(None, description="Уровень для TCP")
    bluetooth_level: Optional[str] = Field(None, description="Уровень для Bluetooth")
    enable_console: bool = Field(False, description="Включить вывод в консоль")
    max_days_keep: int = Field(14, description="Количество дней хранения логов", ge=1, le=365)


class ChangeLabelRequest(BaseModel):
    """Изменение метки драйвера для логирования"""
    label: str = Field(..., description="Метка драйвера (используется в логах с модификатором %L)", max_length=50)


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========

@router.post("/logging", response_model=StatusResponse)
async def configure_logging(
    request: LoggingConfigRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Настроить логирование драйвера АТОЛ.

    Драйвер использует библиотеку log4cpp для логирования.

    **Уровни логирования:**
    - **ERROR** - только ошибки
    - **INFO** - базовое логирование
    - **DEBUG** - расширенное логирование с деталями протокола обмена

    **Категории логов:**
    - **FiscalPrinter** - высокоуровневый лог работы с драйвером
    - **Transport** - лог обмена драйвера с ККТ
    - **EthernetOverTransport** - лог обмена ККТ с ОФД через драйвер
    - **DeviceDebug** - отладочный вывод ККТ
    - **USB** - низкоуровневый лог обмена по USB
    - **COM** - низкоуровневый лог обмена по RS232/VCOM/TTY
    - **TCP** - низкоуровневый лог обмена по TCP/IP
    - **Bluetooth** - низкоуровневый лог обмена по Bluetooth

    **Расположение логов:**
    - Windows: `%APPDATA%/ATOL/drivers10/logs/`
    - Linux: `~/.atol/drivers10/logs/`
    - macOS: `~/Library/Application Support/ru.atol.drivers10/logs/`

    **Файлы логов:**
    - `fptr10.log` - основной лог драйвера
    - `ofd.log` - лог обмена с ОФД
    - `device_debug.log` - отладочный вывод устройства
    - `fptr1C.log` - лог интеграции с 1С

    **Примеры:**
    ```json
    // Базовое логирование
    {"root_level": "INFO", "fiscal_printer_level": "INFO", "transport_level": "INFO"}

    // Расширенное логирование с деталями протокола
    {"root_level": "DEBUG", "fiscal_printer_level": "DEBUG", "transport_level": "DEBUG"}

    // Только ошибки
    {"root_level": "ERROR"}

    // Логирование с выводом в консоль
    {"root_level": "INFO", "fiscal_printer_level": "INFO", "enable_console": true}
    ```

    **Внимание:** Не рекомендуется включать DEBUG для низкоуровневых категорий
    (USB, COM, TCP, Bluetooth) без особой необходимости - это может замедлить работу!
    """
    return redis.execute_command('configure_logging', request.model_dump(exclude_none=True))


@router.post("/label", response_model=StatusResponse)
async def change_driver_label(
    request: ChangeLabelRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Изменить метку драйвера для логирования.

    Метка драйвера - это идентификатор, который добавляется в каждую строку лога
    (если в формате лога присутствует модификатор `%L`).

    **Зачем нужна метка:**
    - Разделение логов при работе с несколькими ККТ
    - Идентификация экземпляра драйвера в мультипоточных приложениях
    - Упрощение отладки

    **Примеры:**
    ```json
    // Метка для кассы №1
    {"label": "KASSA-01"}

    // Метка для конкретного терминала
    {"label": "TERMINAL-MAIN"}

    // Метка с идентификатором пользователя
    {"label": "USER-12345"}
    ```

    **Использование в формате лога:**
    ```
    %d{%Y.%m.%d %H:%M:%S.%l} T:%t %L %-5p [%c] %m%n
    ```
    Где `%L` будет заменен на метку.
    """
    return redis.execute_command('change_driver_label', request.model_dump())


@router.get("/logging/defaults", response_model=StatusResponse)
async def get_default_logging_config(redis: RedisClient = Depends(get_redis_client)):
    """
    Получить настройки логирования по умолчанию.

    Возвращает стандартную конфигурацию логирования драйвера АТОЛ:
    - rootCategory: ERROR
    - FiscalPrinter: INFO
    - Transport: INFO
    - EthernetOverTransport: INFO (в ofd.log)
    - DeviceDebug: INFO (в device_debug.log)

    Логи хранятся 14 дней с автоматической ротацией.
    """
    return redis.execute_command('get_default_logging_config')
