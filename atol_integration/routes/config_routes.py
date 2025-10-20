"""
REST API endpoint'ы для настройки драйвера и логирования
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client
from ..api.routing import RouteDTO, RouterFactory


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


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def configure_logging(
    request: LoggingConfigRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Настроить логирование драйвера АТОЛ"""
    return redis.execute_command('configure_logging', device_id=device_id, kwargs=request.model_dump(exclude_none=True))


async def change_driver_label(
    request: ChangeLabelRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Изменить метку драйвера для логирования"""
    return redis.execute_command('change_driver_label', device_id=device_id, kwargs=request.model_dump())


async def get_default_logging_config(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Получить настройки логирования по умолчанию"""
    return redis.execute_command('get_default_logging_config', device_id=device_id)


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

CONFIG_ROUTES = [
    RouteDTO(
        path="/logging",
        endpoint=configure_logging,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Настроить логирование",
        description="Настроить логирование драйвера АТОЛ (уровни логов, категории, консольный вывод)",
        responses={
            status.HTTP_200_OK: {
                "description": "Логирование успешно настроено",
            },
        },
    ),
    RouteDTO(
        path="/label",
        endpoint=change_driver_label,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Изменить метку драйвера",
        description="Изменить метку драйвера для идентификации в логах (используется с модификатором %L в формате лога)",
        responses={
            status.HTTP_200_OK: {
                "description": "Метка драйвера успешно изменена",
            },
        },
    ),
    RouteDTO(
        path="/logging/defaults",
        endpoint=get_default_logging_config,
        response_model=StatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Настройки логирования по умолчанию",
        description="Получить стандартную конфигурацию логирования драйвера АТОЛ",
        responses={
            status.HTTP_200_OK: {
                "description": "Настройки логирования получены",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/config',
    tags=['Configuration & Logging'],
    routes=CONFIG_ROUTES,
)
