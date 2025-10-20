"""
REST API endpoint'ы для управления подключением к ККТ
"""
from typing import Optional, Dict, Any
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


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


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def open_connection(
    request: OpenConnectionRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Открыть логическое соединение с ККТ"""
    return await pubsub_command_util(redis, device_id=device_id, command='connection_open', kwargs={'settings': request.settings})


async def close_connection(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Закрыть логическое соединение с ККТ"""
    return await pubsub_command_util(redis, device_id=device_id, command='connection_close')


async def is_connection_opened(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Проверить состояние логического соединения"""
    return await pubsub_command_util(redis, device_id=device_id, command='connection_is_opened')


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

CONNECTION_ROUTES = [
    RouteDTO(
        path="/open",
        endpoint=open_connection,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть соединение",
        description="Открыть логическое соединение с кассовым аппаратом",
        responses={
            status.HTTP_200_OK: {
                "description": "Соединение успешно открыто",
            },
        },
    ),
    RouteDTO(
        path="/close",
        endpoint=close_connection,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Закрыть соединение",
        description="Закрыть логическое соединение с кассовым аппаратом",
        responses={
            status.HTTP_200_OK: {
                "description": "Соединение успешно закрыто",
            },
        },
    ),
    RouteDTO(
        path="/is-opened",
        endpoint=is_connection_opened,
        response_model=ConnectionStatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Проверить соединение",
        description="Проверить состояние логического соединения с ККТ",
        responses={
            status.HTTP_200_OK: {
                "description": "Статус соединения получен",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/connection',
    tags=['Connection'],
    routes=CONNECTION_ROUTES,
)
