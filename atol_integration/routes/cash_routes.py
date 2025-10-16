"""
REST API endpoint'ы для кассовых операций (cash operations)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/cash", tags=["Cash Operations"])


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


# ========== ОПЕРАЦИИ С НАЛИЧНЫМИ ==========

@router.post("/in", response_model=CashOperationResponse)
async def cash_in(
    request: CashOperationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Внесение наличных в кассу.
    """
    return redis.execute_command('cash_in', device_id=device_id, kwargs=request.model_dump())


@router.post("/out", response_model=CashOperationResponse)
async def cash_out(
    request: CashOperationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Изъятие наличных из кассы.
    """
    return redis.execute_command('cash_out', device_id=device_id, kwargs=request.model_dump())


@router.get("/sum", response_model=CashSumResponse)
async def get_cash_sum(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Получить сумму наличных в денежном ящике.
    """
    return redis.execute_command('query_data', device_id=device_id, kwargs={'data_type': 3}) # LIBFPTR_DT_CASH_SUM = 3


# ========== УПРАВЛЕНИЕ ДЕНЕЖНЫМ ЯЩИКОМ ==========

@router.post("/drawer/open")
async def open_cash_drawer(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Открыть денежный ящик.
    """
    return redis.execute_command('cash_drawer_open', device_id=device_id)


@router.get("/drawer/status")
async def get_cash_drawer_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Проверить состояние денежного ящика.
    """
    return redis.execute_command('query_data', device_id=device_id, kwargs={'data_type': 1}) # LIBFPTR_DT_STATUS = 1

