"""
FastAPI REST API сервер для АТОЛ ККТ

Модульная структура с разделением endpoint'ов по категориям:
- connection_routes: Управление подключением
- receipt_routes: Операции с чеками
- shift_routes: Операции со сменами
- cash_routes: Кассовые операции
- query_routes: Запросы информации от ККТ
"""
import sys
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import logging

from .driver import AtolDriver, AtolDriverError, ConnectionType
from .schemas import StatusResponse
from .errors import DriverErrorCode, get_error_message
from ..services.query_data import QueryDataService

# Импорты роутеров
from ..routes import connection_routes
from ..routes import receipt_routes
from ..routes import shift_routes
from ..routes import cash_routes
from ..routes import query_routes
from ..routes import print_routes

from ..config.settings import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные экземпляры драйвера и сервисов
driver: Optional[AtolDriver] = None
query_service: Optional[QueryDataService] = None


def get_connection_type(conn_type: str) -> ConnectionType:
    """Преобразовать строку в ConnectionType"""
    mapping = {
        "tcp": ConnectionType.TCP,
        "usb": ConnectionType.USB,
        "serial": ConnectionType.SERIAL,
        "bluetooth": ConnectionType.BLUETOOTH,
    }
    conn_type_lower = conn_type.lower()
    if conn_type_lower not in mapping:
        raise ValueError(f"Неизвестный тип подключения: {conn_type}")
    return mapping[conn_type_lower]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    global driver, query_service

    # Инициализация драйвера при старте
    logger.info("Инициализация АТОЛ драйвера...")
    try:
        # Установить путь к драйверу если указан
        if settings.atol_driver_path:
            sys.path.insert(0, settings.atol_driver_path)
            logger.info(f"Путь к драйверу: {settings.atol_driver_path}")

        driver = AtolDriver()
        query_service = QueryDataService(driver)
        logger.info("✓ Драйвер и сервисы инициализированы")

        # Устанавливаем драйвер для всех роутеров
        connection_routes.set_driver(driver)
        receipt_routes.set_driver(driver)
        shift_routes.set_driver(driver)
        cash_routes.set_driver(driver)
        print_routes.set_driver(driver)
        query_routes.set_query_service(query_service)
        logger.info("✓ Роутеры подключены к драйверу")

        # Автоматическое подключение если настроено
        if settings.atol_host and settings.atol_connection_type:
            try:
                conn_type = get_connection_type(settings.atol_connection_type)
                if conn_type == ConnectionType.TCP:
                    driver.connect(conn_type, settings.atol_host, settings.atol_port)
                elif conn_type == ConnectionType.SERIAL:
                    driver.connect(conn_type, serial_port=settings.atol_serial_port, baudrate=settings.atol_baudrate)
                else:
                    driver.connect(conn_type)
                logger.info(f"✓ Автоподключение к ККТ успешно ({settings.atol_connection_type})")
            except Exception as e:
                logger.warning(f"Автоподключение не удалось: {e}")

    except Exception as e:
        logger.error(f"✗ Ошибка инициализации драйвера: {e}")
        driver = None

    yield

    # Отключение при завершении
    if driver and driver.is_connected():
        driver.disconnect()
        logger.info("✓ Отключение от ККТ")


# Создание FastAPI приложения
app = FastAPI(
    title="АТОЛ ККТ API",
    description="REST API для работы с кассовым оборудованием АТОЛ через драйвер v.10",
    version="0.2.0",
    lifespan=lifespan,
)


def check_driver():
    """Проверить что драйвер инициализирован"""
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Драйвер не инициализирован"
        )


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ==========

# Подключаем все роутеры с префиксами
app.include_router(connection_routes.router)
app.include_router(receipt_routes.router)
app.include_router(shift_routes.router)
app.include_router(cash_routes.router)
app.include_router(print_routes.router)
app.include_router(query_routes.router)

logger.info("✓ Все роутеры подключены к приложению")


# ========== БАЗОВЫЕ ENDPOINTS ==========

@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint с информацией о API"""
    return {
        "name": "АТОЛ ККТ API",
        "version": "0.2.0",
        "status": "running",
        "connected": driver.is_connected() if driver else False,
        "endpoints": {
            "/connection": "Управление подключением к ККТ",
            "/receipt": "Операции с чеками",
            "/shift": "Операции со сменами",
            "/cash": "Кассовые операции (внесение/изъятие)",
            "/print": "Нефискальная печать (текст, штрихкоды, картинки)",
            "/query": "Запросы информации от ККТ",
            "/docs": "Swagger UI документация",
            "/redoc": "ReDoc документация"
        }
    }


@app.get("/health", tags=["System"])
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "driver_initialized": driver is not None,
        "connected": driver.is_connected() if driver else False
    }


# ========== ИНФОРМАЦИЯ О ДРАЙВЕРЕ ==========

@app.get("/driver/version", tags=["Driver"])
async def get_driver_version():
    """Получить версию драйвера"""
    check_driver()

    try:
        version = driver.fptr.version() if driver.fptr else "unknown"
        return {"version": version}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/driver/label", response_model=StatusResponse, tags=["Driver"])
async def change_driver_label(label: str):
    """
    Изменить метку драйвера для логирования

    Метка добавляется в каждую строку лога (если в формате присутствует %L).
    Полезно при работе с несколькими экземплярами драйвера.
    """
    check_driver()

    try:
        driver.change_label(label)
        return StatusResponse(success=True, message=f"Метка драйвера изменена на '{label}'")

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/driver/error", tags=["Driver"])
async def get_last_error():
    """
    Получить последнюю ошибку драйвера

    Каждый метод драйвера возвращает индикатор результата (0 или -1).
    При ошибке можно получить код и описание через errorCode() и errorDescription().
    """
    check_driver()

    try:
        error_code = driver.fptr.errorCode()
        error_description = driver.fptr.errorDescription()

        return {
            "error_code": error_code,
            "error_description": error_description,
            "error_name": get_error_message(error_code) if error_code != 0 else "OK"
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/driver/error/reset", response_model=StatusResponse, tags=["Driver"])
async def reset_error():
    """
    Сбросить информацию о последней ошибке

    Явно очищает информацию о последней ошибке драйвера.
    """
    check_driver()

    try:
        driver.fptr.resetError()
        return StatusResponse(success=True, message="Информация об ошибке сброшена")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/driver/errors/codes", tags=["Driver"])
async def list_error_codes():
    """
    Список всех кодов ошибок драйвера

    Возвращает полный справочник кодов ошибок (000-603) с описаниями.
    """
    return {
        "error_codes": [
            {
                "code": code.value,
                "name": code.name,
                "message": get_error_message(code.value)
            }
            for code in DriverErrorCode
            if code.value <= 700  # Ограничиваем до документированных кодов
        ]
    }


# ========== ВСПОМОГАТЕЛЬНЫЕ ОПЕРАЦИИ ==========

@app.post("/device/beep", response_model=StatusResponse, tags=["Device"])
async def beep():
    """Издать звуковой сигнал"""
    if driver is None or not driver.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Нет подключения к ККТ"
        )

    try:
        driver.beep()
        return StatusResponse(success=True, message="Сигнал подан")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/device/play-portal", response_model=StatusResponse, tags=["Device"])
async def play_portal_melody():
    """
    Сыграть мелодию из Portal 2 через динамик ККТ! 🎵

    "Well here we are again, it's always such a pleasure..."
    """
    if driver is None or not driver.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Нет подключения к ККТ"
        )

    try:
        driver.play_portal_melody()
        return StatusResponse(success=True, message="🎵 Мелодия завершена! This was a triumph!")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/device/cut-paper", response_model=StatusResponse, tags=["Device"])
async def cut_paper():
    """Отрезать чек"""
    if driver is None or not driver.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Нет подключения к ККТ"
        )

    try:
        driver.cut_paper()
        return StatusResponse(success=True, message="Чек отрезан")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ОБРАБОТЧИКИ ОШИБОК ==========

@app.exception_handler(AtolDriverError)
async def atol_driver_error_handler(request, exc: AtolDriverError):
    """Обработчик ошибок драйвера с подробной информацией"""
    error_content = {
        "error": "AtolDriverError",
        "detail": str(exc),
    }

    # Добавляем код ошибки и описание если доступны
    if hasattr(exc, 'error_code') and exc.error_code is not None:
        error_content["error_code"] = exc.error_code
        error_content["error_description"] = exc.error_description
        error_content["message"] = exc.message

        # Добавляем ссылку на документацию по ошибке
        error_content["docs_url"] = f"https://integration.atol.ru/api/#!error-{exc.error_code}"

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_content
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "atol_integration.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
