"""
REST API endpoint'ы для операций с кассирами и документами
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


# ========== МОДЕЛИ ДАННЫХ ==========

class OperatorLoginRequest(BaseModel):
    """Регистрация кассира"""
    operator_name: str = Field(..., description="ФИО кассира", max_length=255)
    operator_vatin: Optional[str] = Field(None, description="ИНН кассира (12 цифр)", max_length=12)


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def operator_login(
    request: OperatorLoginRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Зарегистрировать кассира (operatorLogin)"""
    return await pubsub_command_util(redis, device_id=device_id, command='operator_login', kwargs=request.model_dump(exclude_none=True))


async def continue_print(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Допечатать документ (continuePrint)"""
    return await pubsub_command_util(redis, device_id=device_id, command='continue_print')


async def check_document_closed(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """Проверить закрытие документа (checkDocumentClosed)"""
    return await pubsub_command_util(redis, device_id=device_id, command='check_document_closed')


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

OPERATOR_ROUTES = [
    RouteDTO(
        path="/login",
        endpoint=operator_login,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Регистрация кассира",
        description="Зарегистрировать кассира перед выполнением фискальной операции. Рекомендуется вызывать перед каждой операцией (открытие чека, печать отчета и т.д.)",
        responses={
            status.HTTP_200_OK: {
                "description": "Кассир успешно зарегистрирован",
            },
        },
    ),
    RouteDTO(
        path="/continue-print",
        endpoint=continue_print,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Допечатать документ",
        description="Допечатать фискальный документ, который не был допечатан из-за проблем с принтером (закончилась бумага, открыта крышка и т.д.)",
        responses={
            status.HTTP_200_OK: {
                "description": "Документ допечатан",
            },
        },
    ),
    RouteDTO(
        path="/check-document-closed",
        endpoint=check_document_closed,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Проверить закрытие документа",
        description="Проверить, был ли документ успешно закрыт в ФН и напечатан на чековой ленте. Важнейший метод для обеспечения надежности!",
        responses={
            status.HTTP_200_OK: {
                "description": "Состояние документа проверено",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/operator',
    tags=['Operator & Document Operations'],
    routes=OPERATOR_ROUTES,
)
