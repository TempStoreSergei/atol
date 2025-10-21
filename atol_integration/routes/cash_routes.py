"""
REST API endpoint'ы для кассовых операций (cash operations)
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


# ========== МОДЕЛИ ДАННЫХ ==========

class CashOperationRequest(BaseModel):
    """Запрос на операцию с наличными"""
    amount: float = Field(..., description="Сумма операции", gt=0)
    cashier_name: str = Field(..., description="Имя кассира")


class CashOperationResponse(BaseModel):
    """Ответ на операцию с наличными"""
    success: bool
    operation_type: str
    amount: float
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    shift_number: Optional[int] = None
    message: Optional[str] = None


class CashSumResponse(BaseModel):
    """Ответ с суммой наличных в ящике"""
    cash_sum: float
    currency: str = "RUB"


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def cash_in(
    request: CashOperationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Внесение наличных в кассу"""
    command = {
        "device_id": device_id,
        "command": "cash_in",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def cash_out(
    request: CashOperationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Изъятие наличных из кассы"""
    command = {
        "device_id": device_id,
        "command": "cash_out",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def get_cash_sum(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Получить сумму наличных в денежном ящике"""
    command = {
        "device_id": device_id,
        "command": "query_data",
        "kwargs": {"data_type": 3}  # LIBFPTR_DT_CASH_SUM = 3
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def open_cash_drawer(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Открыть денежный ящик"""
    command = {
        "device_id": device_id,
        "command": "cash_drawer_open"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def get_cash_drawer_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Проверить состояние денежного ящика"""
    command = {
        "device_id": device_id,
        "command": "query_data",
        "kwargs": {"data_type": 1}  # LIBFPTR_DT_STATUS = 1
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

CASH_ROUTES = [
    RouteDTO(
        path="/in",
        endpoint=cash_in,
        response_model=CashOperationResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Внесение наличных",
        description="Внести наличные деньги в кассу",
        responses={
            status.HTTP_200_OK: {
                "description": "Наличные успешно внесены",
            },
        },
    ),
    RouteDTO(
        path="/out",
        endpoint=cash_out,
        response_model=CashOperationResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Изъятие наличных",
        description="Изъять наличные из кассы",
        responses={
            status.HTTP_200_OK: {
                "description": "Наличные успешно изъяты",
            },
        },
    ),
    RouteDTO(
        path="/sum",
        endpoint=get_cash_sum,
        response_model=CashSumResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Сумма в ящике",
        description="Получить текущую сумму наличных в денежном ящике",
        responses={
            status.HTTP_200_OK: {
                "description": "Сумма наличных получена",
            },
        },
    ),
    RouteDTO(
        path="/drawer/open",
        endpoint=open_cash_drawer,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть ящик",
        description="Открыть денежный ящик",
        responses={
            status.HTTP_200_OK: {
                "description": "Денежный ящик открыт",
            },
        },
    ),
    RouteDTO(
        path="/drawer/status",
        endpoint=get_cash_drawer_status,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Статус ящика",
        description="Проверить состояние денежного ящика (открыт/закрыт)",
        responses={
            status.HTTP_200_OK: {
                "description": "Статус денежного ящика получен",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/cash',
    tags=['Cash Operations'],
    routes=CASH_ROUTES,
)
