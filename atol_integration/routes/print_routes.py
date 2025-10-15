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


class BeepRequest(BaseModel):
    """Запрос на звуковой сигнал"""
    frequency: int = Field(2000, description="Частота звука в Гц (100-10000)", ge=100, le=10000)
    duration: int = Field(100, description="Длительность звука в мс (10-5000)", ge=10, le=5000)


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


# ========== ЗВУКОВЫЕ СИГНАЛЫ ==========

@router.post("/beep", response_model=StatusResponse)
async def beep(
    request: BeepRequest = BeepRequest(),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Подать звуковой сигнал через динамик ККТ.

    Параметры:
    - **frequency**: Частота звука в Гц (100-10000). По умолчанию 2000 Гц
    - **duration**: Длительность звука в мс (10-5000). По умолчанию 100 мс

    Примеры частот:
    - 262 Гц - До (C4)
    - 294 Гц - Ре (D4)
    - 330 Гц - Ми (E4)
    - 349 Гц - Фа (F4)
    - 392 Гц - Соль (G4)
    - 440 Гц - Ля (A4)
    - 494 Гц - Си (B4)
    - 523 Гц - До (C5)
    """
    return redis.execute_command('beep', request.model_dump())


@router.post("/play-arcane", response_model=StatusResponse)
async def play_arcane_melody(redis: RedisClient = Depends(get_redis_client)):
    """
    Сыграть мелодию "Enemy" из сериала Arcane через динамик ККТ!

    🎵 Everybody wants to be my enemy... 🎵

    Воспроизводит упрощённую версию главной темы из Arcane (Imagine Dragons feat. JID).
    Примерная длительность: ~15 секунд.

    **Внимание**: Во время воспроизведения мелодии ККТ будет занята и не сможет
    выполнять другие операции.
    """
    # Увеличиваем таймаут до 30 секунд, так как мелодия играет ~15 секунд
    return redis.execute_command('play_arcane_melody', timeout=30)
