"""
REST API endpoint'ы для операций с чеками (receipts)
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client
from ..api.driver import TaxType, PaymentType


router = APIRouter(prefix="/receipt", tags=["Receipt"])


# ========== МОДЕЛИ ДАННЫХ ==========

class OpenReceiptRequest(BaseModel):
    """Запрос на открытие чека"""
    receipt_type: int = Field(..., description="Тип чека (0=продажа, 1=возврат продажи, 2=покупка, 3=возврат покупки)")
    cashier_name: str = Field(..., description="Имя кассира")
    customer_contact: Optional[str] = Field(None, description="Email или телефон клиента")


class AddItemRequest(BaseModel):
    """Запрос на добавление позиции в чек"""
    name: str = Field(..., description="Наименование товара/услуги")
    price: float = Field(..., description="Цена за единицу")
    quantity: float = Field(1.0, description="Количество")
    tax_type: int = Field(TaxType.NONE.value, description="Тип НДС (0=без НДС, 1=0%, 2=10%, 3=20%, 4=10/110, 5=20/120)")
    payment_method: int = Field(4, description="Признак способа расчета (1-7)")
    payment_object: int = Field(1, description="Признак предмета расчета (1-13)")


class AddPaymentRequest(BaseModel):
    """Запрос на добавление оплаты"""
    amount: float = Field(..., description="Сумма оплаты")
    payment_type: int = Field(PaymentType.CASH.value, description="Тип оплаты (0=наличные, 1=электронные, 2=предоплата, 3=кредит, 4=прочее)")


class CloseReceiptResponse(BaseModel):
    """Ответ на закрытие чека с фискальными данными"""
    success: bool
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    # ... другие поля


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ОСНОВНЫЕ ОПЕРАЦИИ С ЧЕКАМИ ==========

@router.post("/open")
async def open_receipt(
    request: OpenReceiptRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Открыть новый чек.
    """
    return redis.execute_command('receipt_open', request.model_dump())


@router.post("/add-item")
async def add_item(
    request: AddItemRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Добавить позицию в открытый чек.
    """
    return redis.execute_command('receipt_add_item', request.model_dump())


@router.post("/add-payment")
async def add_payment(
    request: AddPaymentRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Добавить оплату в открытый чек.
    """
    return redis.execute_command('receipt_add_payment', request.model_dump())


@router.post("/close", response_model=CloseReceiptResponse)
async def close_receipt(redis: RedisClient = Depends(get_redis_client)):
    """
    Закрыть чек и напечатать.
    """
    return redis.execute_command('receipt_close')


@router.post("/cancel")
async def cancel_receipt(redis: RedisClient = Depends(get_redis_client)):
    """
    Отменить открытый чек.
    """
    return redis.execute_command('receipt_cancel')

