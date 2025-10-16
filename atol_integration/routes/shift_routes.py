"""
REST API endpoint'ы для операций со сменами (shifts)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/shift", tags=["Shift"])


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


# ========== ОСНОВНЫЕ ОПЕРАЦИИ СО СМЕНАМИ ==========

@router.post("/open")
async def open_shift(
    request: OpenShiftRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Открыть новую смену.
    """
    return redis.execute_command('shift_open', device_id=device_id, kwargs={'cashier_name': request.cashier_name})


@router.post("/close", response_model=CloseShiftResponse)
async def close_shift(
    cashier_name: str,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Закрыть текущую смену (Z-отчет).
    """
    return redis.execute_command('shift_close', device_id=device_id, kwargs={'cashier_name': cashier_name})


@router.get("/status", response_model=ShiftStatusResponse)
async def get_shift_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Получить статус текущей смены.
    """
    return redis.execute_command('shift_get_status', device_id=device_id)


@router.post("/x-report", response_model=XReportResponse)
async def print_x_report(
    cashier_name: str,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Напечатать X-отчет (отчет без гашения).
    """
    return redis.execute_command('shift_print_x_report', device_id=device_id, kwargs={'cashier_name': cashier_name})

