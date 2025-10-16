"""
REST API endpoint'ы для управления подключением к ККТ
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/connection", tags=["Connection"])


# ========== МОДЕЛИ ДАННЫХ ==========

class OpenConnectionRequest(BaseModel):
    """Запрос на открытие соединения"""
    settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Настройки подключения (IPAddress, IPPort, ComFile, BaudRate и т.д.)"
    )


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


class ConnectionStatusResponse(BaseModel):
    """Статус подключения"""
    is_opened: bool
    message: str


class DeviceInfoResponse(BaseModel):
    """Информация об устройстве"""
    serial_number: Optional[str] = None
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None
    fn_number: Optional[str] = None
    fn_lifetime_state: Optional[int] = None
    registration_number: Optional[str] = None
    inn: Optional[str] = None


# ========== УПРАВЛЕНИЕ СОЕДИНЕНИЕМ ==========

@router.post("/open")
async def open_connection(
    request: OpenConnectionRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Открыть логическое соединение с ККТ.
    Команда отправляется в очередь Redis для асинхронного выполнения.
    """
    return redis.execute_command('connection_open', device_id=device_id, kwargs={'settings': request.settings})


@router.post("/close")
async def close_connection(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Закрыть логическое соединение с ККТ.
    """
    return redis.execute_command('connection_close', device_id=device_id)


@router.get("/is-opened", response_model=ConnectionStatusResponse)
async def is_connection_opened(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Проверить состояние логического соединения.
    """
    return redis.execute_command('connection_is_opened', device_id=device_id)
