"""
REST API endpoint'ы для операций со сменами (shifts)
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


# ========== МОДЕЛИ ДАННЫХ ==========

class OpenShiftRequest(BaseModel):
    """Запрос на открытие смены"""
    cashier_name: str = Field(..., description="Имя кассира")


class CloseShiftResponse(BaseModel):
    """Ответ на закрытие смены с данными"""
    success: bool
    shift_number: Optional[int] = None
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    fiscal_storage_number: Optional[str] = None
    total_receipts: Optional[int] = None
    message: Optional[str] = None


class ShiftStatusResponse(BaseModel):
    """Статус смены"""
    shift_opened: bool
    shift_number: Optional[int] = None
    shift_expired: bool = False
    hours_since_open: Optional[int] = None
    receipts_count: Optional[int] = None


class XReportResponse(BaseModel):
    """Ответ на X-отчет"""
    success: bool
    shift_number: Optional[int] = None
    receipts_count: Optional[int] = None
    total_sales: Optional[float] = None
    total_returns: Optional[float] = None
    cash_in_drawer: Optional[float] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def open_shift(
    request: OpenShiftRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Открыть новую смену"""
    return await pubsub_command_util(redis, device_id=device_id, command='shift_open', kwargs={'cashier_name': request.cashier_name})


async def close_shift(
    cashier_name: str,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Закрыть текущую смену (Z-отчет)"""
    return await pubsub_command_util(redis, device_id=device_id, command='shift_close', kwargs={'cashier_name': cashier_name})


async def get_shift_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Получить статус текущей смены"""
    return await pubsub_command_util(redis, device_id=device_id, command='shift_get_status')


async def print_x_report(
    cashier_name: str,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Напечатать X-отчет (отчет без гашения)"""
    return await pubsub_command_util(redis, device_id=device_id, command='shift_print_x_report', kwargs={'cashier_name': cashier_name})


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

SHIFT_ROUTES = [
    RouteDTO(
        path="/open",
        endpoint=open_shift,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть смену",
        description="Открыть новую рабочую смену на кассе",
        responses={
            status.HTTP_200_OK: {
                "description": "Смена успешно открыта",
            },
        },
    ),
    RouteDTO(
        path="/close",
        endpoint=close_shift,
        response_model=CloseShiftResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Закрыть смену",
        description="Закрыть смену с формированием Z-отчета",
        responses={
            status.HTTP_200_OK: {
                "description": "Смена успешно закрыта, Z-отчет сформирован",
            },
        },
    ),
    RouteDTO(
        path="/status",
        endpoint=get_shift_status,
        response_model=ShiftStatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Статус смены",
        description="Получить информацию о текущей смене",
        responses={
            status.HTTP_200_OK: {
                "description": "Статус смены получен",
            },
        },
    ),
    RouteDTO(
        path="/x-report",
        endpoint=print_x_report,
        response_model=XReportResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="X-отчет",
        description="Напечатать X-отчет без закрытия смены",
        responses={
            status.HTTP_200_OK: {
                "description": "X-отчет успешно напечатан",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/shift',
    tags=['Shift'],
    routes=SHIFT_ROUTES,
)
