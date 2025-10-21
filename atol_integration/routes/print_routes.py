"""
REST API endpoint'ы для нефискальной печати
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


# ========== МОДЕЛИ ДАННЫХ ==========

class PrintTextRequest(BaseModel):
    """Запрос на печать текста со всеми параметрами"""
    text: str = Field("", description="Строка для печати")
    alignment: int = Field(0, description="Выравнивание: 0=влево (LIBFPTR_ALIGNMENT_LEFT), 1=по центру (CENTER), 2=вправо (RIGHT)")
    wrap: int = Field(0, description="Перенос строки: 0=не переносить (LIBFPTR_TW_NONE), 1=по словам (TW_WORDS), 2=по символам (TW_CHARS)")
    font: Optional[int] = Field(None, description="Номер шрифта (зависит от модели ККТ)")
    double_width: Optional[bool] = Field(None, description="Двойная ширина шрифта")
    double_height: Optional[bool] = Field(None, description="Двойная высота шрифта")
    linespacing: Optional[int] = Field(None, description="Межстрочный интервал")
    brightness: Optional[int] = Field(None, description="Яркость печати")
    defer: int = Field(0, description="Отложенная печать: 0=нет (LIBFPTR_DEFER_NONE), 1=перед чеком (PRE), 2=после чека (POST), 3=рядом с ШК (OVERLAY)")


class PrintFeedRequest(BaseModel):
    """Запрос на промотку ленты"""
    lines: int = Field(1, description="Количество пустых строк для промотки", ge=1, le=100)


class PrintBarcodeRequest(BaseModel):
    """Запрос на печать штрихкода со всеми параметрами"""
    barcode: str = Field(..., description="Данные штрихкода (до 500 символов)", max_length=500)
    barcode_type: int = Field(
        17,
        description=(
            "Тип штрихкода:\n"
            "Одномерные: 0=EAN-8, 1=EAN-13, 2=UPC-A, 3=UPC-E, 4=Code39, 5=Code93, 6=Code128, "
            "7=Codabar, 8=ITF, 9=ITF-14, 10=GS1-128, 11=Code39Extended\n"
            "Двумерные: 17=QR (LIBFPTR_BT_QR), 18=PDF417, 19=AZTEC"
        )
    )
    alignment: int = Field(0, description="Выравнивание: 0=влево, 1=по центру, 2=вправо")
    scale: int = Field(2, description="Коэффициент увеличения (1-10)", ge=1, le=10)
    left_margin: Optional[int] = Field(None, description="Дополнительный отступ слева в пикселях")
    invert: Optional[bool] = Field(None, description="Инверсия цвета")
    height: Optional[int] = Field(None, description="Высота штрихкода в пикселях (для одномерных)")
    print_text: Optional[bool] = Field(None, description="Печать данных ШК под штрихкодом (для одномерных)")
    correction: Optional[int] = Field(None, description="Коррекция: 0=по умолчанию, 1=минимум, 2-3 (QR/AZTEC), 4-8 (PDF417)")
    version: Optional[int] = Field(None, description="Версия QR-кода (1-40) или Aztec")
    columns: Optional[int] = Field(None, description="Количество столбцов PDF417")
    defer: int = Field(0, description="Отложенная печать: 0=нет, 1=перед чеком, 2=после чека")


class PrintPictureRequest(BaseModel):
    """Запрос на печать картинки из файла"""
    filename: str = Field(..., description="Путь к файлу картинки (bmp или png без прозрачности)")
    alignment: int = Field(0, description="Выравнивание: 0=влево, 1=по центру, 2=вправо")
    scale_percent: int = Field(100, description="Масштаб в процентах", ge=1, le=1000)
    left_margin: Optional[int] = Field(None, description="Дополнительный отступ слева в пикселях")


class PrintPictureByNumberRequest(BaseModel):
    """Запрос на печать картинки из памяти ККТ"""
    picture_number: int = Field(..., description="Номер картинки в памяти ККТ (отсчёт от 0)")
    alignment: int = Field(0, description="Выравнивание: 0=влево, 1=по центру, 2=вправо")
    left_margin: Optional[int] = Field(None, description="Дополнительный отступ слева в пикселях")
    defer: int = Field(0, description="Отложенная печать: 0=нет, 1=перед чеком, 2=после чека")


class BeepRequest(BaseModel):
    """Запрос на звуковой сигнал"""
    frequency: int = Field(2000, description="Частота звука в Гц (100-10000)", ge=100, le=10000)
    duration: int = Field(100, description="Длительность звука в мс (10-5000)", ge=10, le=5000)


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def print_text(
    request: PrintTextRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Напечатать строку текста с форматированием.

    **Параметры:**
    - **text**: Строка для печати
    - **alignment**: Выравнивание (0=влево, 1=центр, 2=вправо)
    - **wrap**: Перенос строк (0=нет, 1=по словам, 2=по символам)
    - **font**: Номер шрифта (опционально, зависит от модели ККТ)
    - **double_width**: Двойная ширина шрифта (опционально)
    - **double_height**: Двойная высота шрифта (опционально)
    - **linespacing**: Межстрочный интервал (опционально)
    - **brightness**: Яркость печати (опционально)
    - **defer**: Отложенная печать (0=нет, 1=перед чеком, 2=после чека, 3=рядом с ШК)

    **Примеры:**
    ```json
    // Простой текст
    {"text": "Привет, мир!"}

    // Текст по центру с двойной шириной
    {"text": "ВНИМАНИЕ!", "alignment": 1, "double_width": true}

    // Текст с переносом по словам
    {"text": "Очень длинная строка которая не поместится", "wrap": 1}
    ```
    """
    command = {
        "device_id": device_id,
        "command": "print_text",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def feed_line(
    request: PrintFeedRequest = PrintFeedRequest(),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Промотать чековую ленту на N пустых строк.

    **Внимание:** Не рекомендуется печатать вне открытых документов!
    """
    command = {
        "device_id": device_id,
        "command": "print_feed",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def print_barcode(
    request: PrintBarcodeRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Напечатать штрихкод.

    **Типы штрихкодов:**

    *Одномерные:*
    - 0 = EAN-8
    - 1 = EAN-13
    - 2 = UPC-A
    - 3 = UPC-E
    - 4 = Code 39
    - 5 = Code 93
    - 6 = Code 128
    - 7 = Codabar
    - 8 = ITF (Interleaved 2of5)
    - 9 = ITF-14
    - 10 = GS1-128 (EAN-128)
    - 11 = Code 39 Extended

    *Двумерные:*
    - 17 = QR-код (по умолчанию)
    - 18 = PDF417
    - 19 = AZTEC

    **Примеры:**
    ```json
    // Простой QR-код
    {"barcode": "https://example.com", "barcode_type": 17}

    // EAN-13 с увеличением
    {"barcode": "4607123456789", "barcode_type": 1, "scale": 3}

    // QR по центру с коррекцией
    {"barcode": "Большой текст", "barcode_type": 17, "alignment": 1, "correction": 3, "scale": 4}
    ```

    **GS1-128:** AI заключаются в квадратные скобки:
    ```json
    {"barcode": "[01]98898765432106[3202]012345[15]991231", "barcode_type": 10}
    ```
    """
    command = {
        "device_id": device_id,
        "command": "print_barcode",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def print_picture(
    request: PrintPictureRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Напечатать картинку из файла.

    **Поддерживаемые форматы:** BMP и PNG без прозрачности

    **Примеры:**
    ```json
    // Печать логотипа по центру
    {"filename": "/path/to/logo.png", "alignment": 1, "scale_percent": 100}

    // Уменьшенная картинка
    {"filename": "C:\\\\images\\\\receipt_header.bmp", "scale_percent": 50}
    ```

    **Внимание:** Не рекомендуется печатать вне открытых документов!
    """
    command = {
        "device_id": device_id,
        "command": "print_picture",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def print_picture_by_number(
    request: PrintPictureByNumberRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Напечатать картинку из памяти ККТ.

    Картинки должны быть предварительно загружены в память ККТ.
    Нумерация картинок начинается с 0.

    **Примеры:**
    ```json
    // Печать логотипа (картинка №0)
    {"picture_number": 0, "alignment": 1}

    // Картинка перед чеком
    {"picture_number": 1, "defer": 1}
    ```

    **Внимание:** Не рекомендуется печатать вне открытых документов!
    """
    command = {
        "device_id": device_id,
        "command": "print_picture_by_number",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def open_nonfiscal_document(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Открыть нефискальный документ.

    **Важно:** Нефискальный документ - это чек, который не передается в ОФД.
    Используется для печати служебной информации, логотипов, объявлений и т.д.

    **Обязательно закрывайте документ** после печати с помощью `/document/close`!

    **Порядок работы:**
    1. Открыть документ (`/document/open`)
    2. Печатать текст, штрихкоды, картинки (`/text`, `/barcode`, `/picture`)
    3. Закрыть документ (`/document/close`)
    """
    command = {
        "device_id": device_id,
        "command": "open_nonfiscal_document"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def close_nonfiscal_document(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Закрыть нефискальный документ.

    Завершает печать нефискального документа и отрезает чек.
    """
    command = {
        "device_id": device_id,
        "command": "close_nonfiscal_document"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def cut_paper(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Отрезать чековую ленту.

    Используется для отрезания чека после завершения печати.
    """
    command = {
        "device_id": device_id,
        "command": "cut_paper"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def open_cash_drawer(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Открыть денежный ящик.

    Подает сигнал на открытие денежного ящика, подключенного к ККТ.
    """
    command = {
        "device_id": device_id,
        "command": "open_cash_drawer"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def beep(
    request: BeepRequest = BeepRequest(),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
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
    command = {
        "device_id": device_id,
        "command": "beep",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def play_arcane_melody(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Сыграть мелодию "Enemy" из сериала Arcane через динамик ККТ!

    🎵 Everybody wants to be my enemy... 🎵

    Воспроизводит упрощённую версию главной темы из Arcane (Imagine Dragons feat. JID).
    Примерная длительность: ~15 секунд.

    **Внимание**: Во время воспроизведения мелодии ККТ будет занята и не сможет
    выполнять другие операции.
    """
    command = {
        "device_id": device_id,
        "command": "play_arcane_melody"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

PRINT_ROUTES = [
    RouteDTO(
        path="/text",
        endpoint=print_text,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Печать текста",
        description="Напечатать строку текста с форматированием",
        responses={
            status.HTTP_200_OK: {
                "description": "Текст успешно напечатан",
            },
        },
    ),
    RouteDTO(
        path="/feed",
        endpoint=feed_line,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Промотка ленты",
        description="Промотать чековую ленту на N пустых строк",
        responses={
            status.HTTP_200_OK: {
                "description": "Лента успешно промотана",
            },
        },
    ),
    RouteDTO(
        path="/barcode",
        endpoint=print_barcode,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Печать штрихкода",
        description="Напечатать одномерный или двумерный штрихкод (QR, EAN-13, PDF417, и др.)",
        responses={
            status.HTTP_200_OK: {
                "description": "Штрихкод успешно напечатан",
            },
        },
    ),
    RouteDTO(
        path="/picture",
        endpoint=print_picture,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Печать картинки из файла",
        description="Напечатать картинку из файла (BMP или PNG без прозрачности)",
        responses={
            status.HTTP_200_OK: {
                "description": "Картинка успешно напечатана",
            },
        },
    ),
    RouteDTO(
        path="/picture-by-number",
        endpoint=print_picture_by_number,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Печать картинки из памяти",
        description="Напечатать картинку из памяти ККТ по номеру",
        responses={
            status.HTTP_200_OK: {
                "description": "Картинка успешно напечатана",
            },
        },
    ),
    RouteDTO(
        path="/document/open",
        endpoint=open_nonfiscal_document,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть нефискальный документ",
        description="Открыть нефискальный документ для печати",
        responses={
            status.HTTP_200_OK: {
                "description": "Нефискальный документ открыт",
            },
        },
    ),
    RouteDTO(
        path="/document/close",
        endpoint=close_nonfiscal_document,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Закрыть нефискальный документ",
        description="Закрыть нефискальный документ и отрезать чек",
        responses={
            status.HTTP_200_OK: {
                "description": "Нефискальный документ закрыт",
            },
        },
    ),
    RouteDTO(
        path="/cut",
        endpoint=cut_paper,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Отрезать чек",
        description="Отрезать чековую ленту",
        responses={
            status.HTTP_200_OK: {
                "description": "Лента отрезана",
            },
        },
    ),
    RouteDTO(
        path="/open-drawer",
        endpoint=open_cash_drawer,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть денежный ящик",
        description="Подать сигнал на открытие денежного ящика",
        responses={
            status.HTTP_200_OK: {
                "description": "Денежный ящик открыт",
            },
        },
    ),
    RouteDTO(
        path="/beep",
        endpoint=beep,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Звуковой сигнал",
        description="Подать звуковой сигнал через динамик ККТ",
        responses={
            status.HTTP_200_OK: {
                "description": "Звуковой сигнал воспроизведён",
            },
        },
    ),
    RouteDTO(
        path="/play-arcane",
        endpoint=play_arcane_melody,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Мелодия Arcane",
        description="Сыграть мелодию 'Enemy' из сериала Arcane",
        responses={
            status.HTTP_200_OK: {
                "description": "Мелодия успешно воспроизведена",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/print',
    tags=['Non-Fiscal Printing'],
    routes=PRINT_ROUTES,
)
