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

@app.post("/connection/open", response_model=StatusResponse, tags=["Connection"])
async def open_connection(request: ConnectRequest):
    """
    Установить соединение с ККТ (fptr.open())

    После настройки рабочего экземпляра можно подключиться к ККТ.
    До вызова данного метода все другие операции с ККТ будут завершаться
    с ошибкой LIBFPTR_ERROR_CONNECTION_DISABLED.
    """
    check_driver()

    try:
        conn_type = get_connection_type(request.connection_type)

        if conn_type == ConnectionType.TCP:
            driver.connect(conn_type, request.host, request.port)
        elif conn_type == ConnectionType.SERIAL:
            driver.connect(conn_type, serial_port=request.serial_port, baudrate=request.baudrate)
        else:
            driver.connect(conn_type)

        return StatusResponse(success=True, message="Соединение установлено")

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/connection/close", response_model=StatusResponse, tags=["Connection"])
async def close_connection():
    """
    Завершить соединение с ККТ (fptr.close())

    Драйвер вернется в изначальное состояние, как до вызова open().
    Канал с ОФД будет закрыт и отправка документов в ОФД будет прервана.
    """
    check_driver()

    try:
        driver.disconnect()
        return StatusResponse(success=True, message="Соединение завершено")
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/connection/is-opened", tags=["Connection"])
async def is_connection_opened():
    """
    Проверить состояние логического соединения (fptr.isOpened())

    Результат не отражает текущее состояние подключения - если с ККТ была разорвана связь,
    то метод все также будет возвращать true, но методы, выполняющие операции над ККТ,
    будут возвращать ошибку LIBFPTR_ERROR_NO_CONNECTION.
    """
    check_driver()
    return {
        "is_opened": driver.is_connected(),
        "note": "Возвращает логическое состояние, а не фактическое подключение"
    }


@app.get("/connection/status", tags=["Connection"])
async def connection_status():
    """Получить статус подключения (устаревший endpoint, используйте /connection/is-opened)"""
    check_driver()
    return {"connected": driver.is_connected()}


# ========== ЗАПРОСЫ ИНФОРМАЦИИ О ККТ (queryData) ==========

@app.get("/query/status", tags=["Query"])
async def query_status():
    """
    Запрос общей информации и статуса ККТ (LIBFPTR_DT_STATUS)

    Возвращает полную информацию о состоянии ККТ: номер кассира, смены, чека,
    состояние ФН, бумаги, денежного ящика, модель, версию ПО и многое другое.
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса статуса: {driver.fptr.errorDescription()}")

        return {
            "operator_id": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID),
            "logical_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER),
            "shift_state": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
            "model": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL),
            "mode": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODE),
            "submode": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE),
            "receipt_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER),
            "document_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            "shift_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            "receipt_type": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
            "document_type": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE),
            "line_length": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH),
            "line_length_pix": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX),
            "receipt_sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
            "is_fiscal_device": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FISCAL),
            "is_fiscal_fn": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_FISCAL),
            "is_fn_present": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_PRESENT),
            "is_invalid_fn": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN),
            "is_cashdrawer_opened": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
            "is_paper_present": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
            "is_paper_near_end": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
            "is_cover_opened": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
            "is_printer_connection_lost": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_CONNECTION_LOST),
            "is_printer_error": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_ERROR),
            "is_cut_error": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CUT_ERROR),
            "is_printer_overheat": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_OVERHEAT),
            "is_device_blocked": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED),
            "date_time": driver.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat(),
            "serial_number": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),
            "model_name": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
            "firmware_version": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/short-status", tags=["Query"])
async def query_short_status():
    """
    Короткий запрос статуса ККТ (LIBFPTR_DT_SHORT_STATUS)

    Возвращает только основные статусы: денежный ящик, бумага, крышка.
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHORT_STATUS)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса статуса: {driver.fptr.errorDescription()}")

        return {
            "is_cashdrawer_opened": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
            "is_paper_present": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
            "is_paper_near_end": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
            "is_cover_opened": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/cash-sum", tags=["Query"])
async def query_cash_sum():
    """
    Запрос суммы наличных в денежном ящике (LIBFPTR_DT_CASH_SUM)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASH_SUM)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "cash_sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/unit-version", tags=["Query"])
async def query_unit_version(unit_type: int):
    """
    Запрос версии модуля (LIBFPTR_DT_UNIT_VERSION)

    unit_type:
    - 0 (LIBFPTR_UT_FIRMWARE): прошивка
    - 1 (LIBFPTR_UT_CONFIGURATION): конфигурация
    - 2 (LIBFPTR_UT_TEMPLATES): движок шаблонов
    - 3 (LIBFPTR_UT_CONTROL_UNIT): блок управления
    - 4 (LIBFPTR_UT_BOOT): загрузчик
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, unit_type)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        response = {
            "unit_version": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }

        # Для конфигурации добавляем версию релиза
        if unit_type == 1:  # LIBFPTR_UT_CONFIGURATION
            response["release_version"] = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_RELEASE_VERSION)

        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/shift-state", tags=["Query"])
async def query_shift_state():
    """
    Запрос состояния смены (LIBFPTR_DT_SHIFT_STATE)

    Состояние смены:
    - 0 (LIBFPTR_SS_CLOSED): смена закрыта
    - 1 (LIBFPTR_SS_OPENED): смена открыта
    - 2 (LIBFPTR_SS_EXPIRED): смена истекла (больше 24 часов)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "shift_state": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
            "shift_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            "date_time": driver.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/receipt-state", tags=["Query"])
async def query_receipt_state():
    """
    Запрос состояния чека (LIBFPTR_DT_RECEIPT_STATE)

    Возвращает информацию об открытом чеке: тип, номер, сумму, остаток, сдачу.
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "receipt_type": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
            "receipt_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER),
            "document_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            "receipt_sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
            "remainder": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_REMAINDER),
            "change": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_CHANGE)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/serial-number", tags=["Query"])
async def query_serial_number():
    """
    Запрос заводского номера ККТ (LIBFPTR_DT_SERIAL_NUMBER)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SERIAL_NUMBER)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "serial_number": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/model-info", tags=["Query"])
async def query_model_info():
    """
    Запрос информации о модели ККТ (LIBFPTR_DT_MODEL_INFO)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_MODEL_INFO)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "model": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL),
            "model_name": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
            "firmware_version": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/date-time", tags=["Query"])
async def query_date_time():
    """
    Запрос текущих даты и времени ККТ (LIBFPTR_DT_DATE_TIME)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_DATE_TIME)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "date_time": driver.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/receipt-line-length", tags=["Query"])
async def query_receipt_line_length():
    """
    Запрос ширины чековой ленты (LIBFPTR_DT_RECEIPT_LINE_LENGTH)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_LINE_LENGTH)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "char_line_length": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH),
            "pix_line_length": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/payment-sum", tags=["Query"])
async def query_payment_sum(receipt_type: int, payment_type: int):
    """
    Запрос суммы платежей за смену (LIBFPTR_DT_PAYMENT_SUM)

    receipt_type: 0-5 (SELL, SELL_RETURN, SELL_CORRECTION, BUY, BUY_RETURN, BUY_CORRECTION)
    payment_type: 0-9 (CASH, ELECTRONICALLY, PREPAID, CREDIT, OTHER, PT_6-10)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_PAYMENT_SUM)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, receipt_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, payment_type)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/cashin-sum", tags=["Query"])
async def query_cashin_sum():
    """Запрос суммы внесений (LIBFPTR_DT_CASHIN_SUM)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHIN_SUM)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/cashout-sum", tags=["Query"])
async def query_cashout_sum():
    """Запрос суммы выплат (LIBFPTR_DT_CASHOUT_SUM)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHOUT_SUM)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"sum": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/cashin-count", tags=["Query"])
async def query_cashin_count():
    """Запрос количества внесений (LIBFPTR_DT_CASHIN_COUNT)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHIN_COUNT)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"count": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/cashout-count", tags=["Query"])
async def query_cashout_count():
    """Запрос количества выплат (LIBFPTR_DT_CASHOUT_COUNT)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHOUT_COUNT)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"count": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/receipt-count", tags=["Query"])
async def query_receipt_count(receipt_type: int):
    """
    Запрос количества чеков (LIBFPTR_DT_RECEIPT_COUNT)

    receipt_type: 0-5 (SELL, SELL_RETURN, SELL_CORRECTION, BUY, BUY_RETURN, BUY_CORRECTION)
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_COUNT)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, receipt_type)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"count": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/mac-address", tags=["Query"])
async def query_mac_address():
    """Запрос MAC-адреса Ethernet (LIBFPTR_DT_MAC_ADDRESS)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_MAC_ADDRESS)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"mac_address": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_MAC_ADDRESS)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/printer-temperature", tags=["Query"])
async def query_printer_temperature():
    """Запрос температуры ТПГ (LIBFPTR_DT_PRINTER_TEMPERATURE)"""
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_PRINTER_TEMPERATURE)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {"temperature": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_PRINTER_TEMPERATURE)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/query/power-source-state", tags=["Query"])
async def query_power_source_state(power_source_type: int):
    """
    Запрос состояния источника питания (LIBFPTR_DT_POWER_SOURCE_STATE)

    power_source_type:
    - 0 (LIBFPTR_PST_POWER_SUPPLY): внешний блок питания
    - 1 (LIBFPTR_PST_RTC_BATTERY): батарея часов
    - 2 (LIBFPTR_PST_BATTERY): встроенные аккумуляторы
    """
    check_connection()

    try:
        from .libfptr10 import IFptr
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_POWER_SOURCE_STATE)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_POWER_SOURCE_TYPE, power_source_type)
        result = driver.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {driver.fptr.errorDescription()}")

        return {
            "battery_charge": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_BATTERY_CHARGE),
            "voltage": driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_VOLTAGE),
            "use_battery": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_USE_BATTERY),
            "is_charging": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_BATTERY_CHARGING),
            "can_print_on_battery": driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CAN_PRINT_WHILE_ON_BATTERY)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ (УСТАРЕВШИЕ) ==========

@app.get("/device/info", response_model=DeviceInfoResponse, tags=["Device"])
async def get_device_info():
    """
    Получить информацию об устройстве (устаревший endpoint)

    Используйте вместо этого: /query/status или /query/model-info
    """
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
