"""
REST API endpoint'ы для нефискальной печати
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/print", tags=["Non-Fiscal Printing"])


# ========== МОДЕЛИ ДАННЫХ ==========

class PrintTextRequest(BaseModel):
    """Запрос на печать текста"""
    text: str = Field(..., description="Текст для печати")
    alignment: int = Field(0, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")
    wrap: int = Field(0, description="Перенос строк (0=нет, 1=по словам, 2=по символам)")


class PrintBarcodeRequest(BaseModel):
    """Запрос на печать штрихкода"""
    barcode: str = Field(..., description="Данные штрихкода")
    barcode_type: int = Field(17, description="Тип штрихкода (17=QR)") # 17 = LIBFPTR_BT_QR
    alignment: int = Field(0, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")
    scale: int = Field(2, description="Коэффициент увеличения (1-10)")


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ПЕЧАТЬ ТЕКСТА ==========

@router.post("/text")
async def print_text(
    request: PrintTextRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Напечатать текст.
    """
    return redis.execute_command('print_text', request.model_dump())


@router.post("/feed")
async def feed_line(
    lines: int = 1,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Промотать ленту (пустые строки).
    """
    return redis.execute_command('print_feed', {'lines': lines})


# ========== ПЕЧАТЬ ШТРИХКОДА ==========

@router.post("/barcode")
async def print_barcode(
    request: PrintBarcodeRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Напечатать штрихкод.
    """
    return redis.execute_command('print_barcode', request.model_dump())

