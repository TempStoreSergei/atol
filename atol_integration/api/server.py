"""
FastAPI REST API сервер для АТОЛ ККТ
"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import logging

from .driver import AtolDriver, AtolDriverError, ConnectionType
from .schemas import *
from .errors import DriverErrorCode, get_error_message
from ..config.settings import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальный экземпляр драйвера
driver: Optional[AtolDriver] = None


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
    global driver

    # Инициализация драйвера при старте
    logger.info("Инициализация АТОЛ драйвера...")
    try:
        # Установить путь к драйверу если указан
        if settings.atol_driver_path:
            sys.path.insert(0, settings.atol_driver_path)
            logger.info(f"Путь к драйверу: {settings.atol_driver_path}")

        driver = AtolDriver()
        logger.info("✓ Драйвер инициализирован")

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


def check_connection():
    """Проверить что есть подключение к ККТ"""
    check_driver()
    if not driver.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Нет подключения к ККТ"
        )


# ========== ENDPOINTS ==========

@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint"""
    return {
        "name": "АТОЛ ККТ API",
        "version": "0.2.0",
        "status": "running",
        "connected": driver.is_connected() if driver else False
    }


@app.get("/health", tags=["System"])
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "driver_initialized": driver is not None,
        "connected": driver.is_connected() if driver else False
    }


# ========== ПОДКЛЮЧЕНИЕ ==========

@app.post("/connect", response_model=StatusResponse, tags=["Connection"])
async def connect(request: ConnectRequest):
    """Подключиться к ККТ"""
    check_driver()

    try:
        conn_type = get_connection_type(request.connection_type)

        if conn_type == ConnectionType.TCP:
            driver.connect(conn_type, request.host, request.port)
        elif conn_type == ConnectionType.SERIAL:
            driver.connect(conn_type, serial_port=request.serial_port, baudrate=request.baudrate)
        else:
            driver.connect(conn_type)

        return StatusResponse(success=True, message="Подключение успешно")

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/disconnect", response_model=StatusResponse, tags=["Connection"])
async def disconnect():
    """Отключиться от ККТ"""
    check_driver()

    try:
        driver.disconnect()
        return StatusResponse(success=True, message="Отключение успешно")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/status", tags=["Connection"])
async def connection_status():
    """Получить статус подключения"""
    check_driver()
    return {"connected": driver.is_connected()}


# ========== ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ ==========

@app.get("/device/info", response_model=DeviceInfoResponse, tags=["Device"])
async def get_device_info():
    """Получить информацию об устройстве"""
    check_connection()

    try:
        info = driver.get_device_info()
        return DeviceInfoResponse(**info)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/shift/status", response_model=ShiftStatusResponse, tags=["Shift"])
async def get_shift_status():
    """Получить статус смены"""
    check_connection()

    try:
        status_data = driver.get_shift_status()
        return ShiftStatusResponse(**status_data)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== УПРАВЛЕНИЕ СМЕНОЙ ==========

@app.post("/shift/open", response_model=ShiftStatusResponse, tags=["Shift"])
async def open_shift(request: OpenShiftRequest):
    """Открыть смену"""
    check_connection()

    try:
        result = driver.open_shift(request.cashier_name)
        return ShiftStatusResponse(**result)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/shift/close", response_model=StatusResponse, tags=["Shift"])
async def close_shift(request: CloseShiftRequest):
    """Закрыть смену (Z-отчет)"""
    check_connection()

    try:
        driver.close_shift(request.cashier_name)
        return StatusResponse(success=True, message="Смена закрыта")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/shift/x-report", response_model=StatusResponse, tags=["Shift"])
async def x_report():
    """Напечатать X-отчет (без гашения)"""
    check_connection()

    try:
        driver.x_report()
        return StatusResponse(success=True, message="X-отчет распечатан")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ОПЕРАЦИИ С ЧЕКАМИ ==========

@app.post("/receipt/open", response_model=StatusResponse, tags=["Receipt"])
async def open_receipt(request: OpenReceiptRequest):
    """Открыть чек"""
    check_connection()

    try:
        driver.open_receipt(
            request.receipt_type,
            request.cashier_name,
            request.email,
            request.phone
        )
        return StatusResponse(success=True, message="Чек открыт")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/receipt/add-item", response_model=StatusResponse, tags=["Receipt"])
async def add_item(request: AddItemRequest):
    """Добавить товар в чек"""
    check_connection()

    try:
        driver.add_item(
            request.name,
            request.price,
            request.quantity,
            request.tax_type,
            request.department,
            request.measure_unit
        )
        return StatusResponse(success=True, message="Товар добавлен")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/receipt/add-payment", response_model=StatusResponse, tags=["Receipt"])
async def add_payment(request: AddPaymentRequest):
    """Добавить оплату"""
    check_connection()

    try:
        driver.add_payment(request.amount, request.payment_type)
        return StatusResponse(success=True, message="Оплата добавлена")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/receipt/close", response_model=ReceiptResponse, tags=["Receipt"])
async def close_receipt():
    """Закрыть и напечатать чек"""
    check_connection()

    try:
        result = driver.close_receipt()
        return ReceiptResponse(**result)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/receipt/cancel", response_model=StatusResponse, tags=["Receipt"])
async def cancel_receipt():
    """Отменить текущий чек"""
    check_connection()

    try:
        driver.cancel_receipt()
        return StatusResponse(success=True, message="Чек отменен")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/receipt/create", response_model=ReceiptResponse, tags=["Receipt"])
async def create_receipt(request: CreateReceiptRequest):
    """Создать и закрыть чек одним запросом"""
    check_connection()

    try:
        # Открываем чек
        driver.open_receipt(
            request.receipt_type,
            request.cashier_name,
            request.email,
            request.phone
        )

        # Добавляем товары
        for item in request.items:
            driver.add_item(
                item.name,
                item.price,
                item.quantity,
                item.tax_type,
                item.department,
                item.measure_unit
            )

        # Добавляем оплаты
        for payment in request.payments:
            driver.add_payment(payment.amount, payment.payment_type)

        # Закрываем чек
        result = driver.close_receipt()
        return ReceiptResponse(**result)

    except AtolDriverError as e:
        # Пытаемся отменить чек при ошибке
        try:
            driver.cancel_receipt()
        except:
            pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ЧЕКИ КОРРЕКЦИИ ==========

@app.post("/correction/open", response_model=StatusResponse, tags=["Correction"])
async def open_correction_receipt(request: OpenCorrectionReceiptRequest):
    """Открыть чек коррекции"""
    check_connection()

    try:
        driver.open_correction_receipt(
            request.correction_type,
            request.base_date,
            request.base_number,
            request.base_name,
            request.cashier_name
        )
        return StatusResponse(success=True, message="Чек коррекции открыт")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/correction/add-item", response_model=StatusResponse, tags=["Correction"])
async def add_correction_item(request: AddCorrectionItemRequest):
    """Добавить позицию в чек коррекции"""
    check_connection()

    try:
        driver.add_correction_item(request.amount, request.tax_type, request.description)
        return StatusResponse(success=True, message="Позиция коррекции добавлена")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ДЕНЕЖНЫЕ ОПЕРАЦИИ ==========

@app.post("/cash/income", response_model=StatusResponse, tags=["Cash"])
async def cash_income(request: CashOperationRequest):
    """Внести наличные в кассу"""
    check_connection()

    try:
        driver.cash_income(request.amount)
        return StatusResponse(success=True, message=f"Внесено {request.amount} руб")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/cash/outcome", response_model=StatusResponse, tags=["Cash"])
async def cash_outcome(request: CashOperationRequest):
    """Выплатить наличные из кассы"""
    check_connection()

    try:
        driver.cash_outcome(request.amount)
        return StatusResponse(success=True, message=f"Выплачено {request.amount} руб")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

@app.post("/device/beep", response_model=StatusResponse, tags=["Device"])
async def beep():
    """Издать звуковой сигнал"""
    check_connection()

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
    check_connection()

    try:
        driver.play_portal_melody()
        return StatusResponse(success=True, message="🎵 Мелодия завершена! This was a triumph!")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/device/open-drawer", response_model=StatusResponse, tags=["Device"])
async def open_cash_drawer():
    """Открыть денежный ящик"""
    check_connection()

    try:
        driver.open_cash_drawer()
        return StatusResponse(success=True, message="Денежный ящик открыт")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/device/cut-paper", response_model=StatusResponse, tags=["Device"])
async def cut_paper():
    """Отрезать чек"""
    check_connection()

    try:
        driver.cut_paper()
        return StatusResponse(success=True, message="Чек отрезан")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ОБРАБОТКА ОШИБОК ДРАЙВЕРА ==========

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


@app.get("/driver/version", tags=["Driver"])
async def get_driver_version():
    """Получить версию драйвера"""
    check_driver()

    try:
        version = driver.fptr.version() if driver.fptr else "unknown"
        return {"version": version}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/driver/label", tags=["Driver"])
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


# ========== ОБРАБОТЧИКИ ОШИБОК ==========

@app.exception_handler(AtolDriverError)
async def atol_driver_error_handler(request, exc: AtolDriverError):
    """Обработчик ошибок драйвера"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "AtolDriverError", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "atol_integration.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
