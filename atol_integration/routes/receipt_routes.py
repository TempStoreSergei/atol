"""
REST API endpoint'ы для операций с чеками (receipts)
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.driver import TaxType, PaymentType
from ..api.routing import RouteDTO, RouterFactory


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


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def open_receipt(
    request: OpenReceiptRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Открыть новый чек"""
    return await pubsub_command_util(redis, device_id=device_id, command='receipt_open', kwargs=request.model_dump())


async def add_item(
    request: AddItemRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Добавить позицию в открытый чек"""
    return await pubsub_command_util(redis, device_id=device_id, command='receipt_add_item', kwargs=request.model_dump())


async def add_payment(
    request: AddPaymentRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Добавить оплату в открытый чек"""
    return await pubsub_command_util(redis, device_id=device_id, command='receipt_add_payment', kwargs=request.model_dump())


async def close_receipt(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Закрыть чек и напечатать"""
    return await pubsub_command_util(redis, device_id=device_id, command='receipt_close')


async def cancel_receipt(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Отменить открытый чек"""
    return await pubsub_command_util(redis, device_id=device_id, command='receipt_cancel')


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

RECEIPT_ROUTES = [
    RouteDTO(
        path="/open",
        endpoint=open_receipt,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть чек",
        description="Открыть новый чек для продажи, возврата, покупки или возврата покупки",
        responses={
            status.HTTP_200_OK: {
                "description": "Чек успешно открыт",
            },
        },
    ),
    RouteDTO(
        path="/add-item",
        endpoint=add_item,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Добавить позицию",
        description="Добавить товар или услугу в открытый чек",
        responses={
            status.HTTP_200_OK: {
                "description": "Позиция успешно добавлена",
            },
        },
    ),
    RouteDTO(
        path="/add-payment",
        endpoint=add_payment,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Добавить оплату",
        description="Добавить оплату в открытый чек (наличные, карта и т.д.)",
        responses={
            status.HTTP_200_OK: {
                "description": "Оплата успешно добавлена",
            },
        },
    ),
    RouteDTO(
        path="/close",
        endpoint=close_receipt,
        response_model=CloseReceiptResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Закрыть чек",
        description="Закрыть и напечатать чек, получить фискальные данные",
        responses={
            status.HTTP_200_OK: {
                "description": "Чек успешно закрыт и напечатан",
            },
        },
    ),
    RouteDTO(
        path="/cancel",
        endpoint=cancel_receipt,
        response_model=None,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Отменить чек",
        description="Отменить открытый чек без печати",
        responses={
            status.HTTP_200_OK: {
                "description": "Чек успешно отменён",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/receipt',
    tags=['Receipt'],
    routes=RECEIPT_ROUTES,
)
