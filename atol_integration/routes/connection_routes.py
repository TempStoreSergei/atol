"""
REST API endpoint'ы для управления подключением к ККТ
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..api.driver import AtolDriver, AtolDriverError
from ..api import libfptr10
IFptr = libfptr10.IFptr

router = APIRouter(prefix="/connection", tags=["Connection"])

# Глобальный экземпляр драйвера (будет установлен из server.py)
driver: Optional[AtolDriver] = None


def set_driver(drv: AtolDriver):
    """Установить экземпляр драйвера для использования в routes"""
    global driver
    driver = drv


def check_driver():
    """Проверить что драйвер инициализирован"""
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Driver not initialized"
        )


# ========== МОДЕЛИ ДАННЫХ ==========

class OpenConnectionRequest(BaseModel):
    """Запрос на открытие соединения"""
    settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Настройки подключения (IPAddress, IPPort, ComFile, BaudRate и т.д.)"
    )


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


class ConnectionStatusResponse(BaseModel):
    """Статус подключения"""
    is_opened: bool
    message: str


class DeviceInfoResponse(BaseModel):
    """Информация об устройстве"""
    serial_number: Optional[str] = None
    model_name: Optional[str] = None
    firmware_version: Optional[str] = None
    fn_number: Optional[str] = None
    fn_lifetime_state: Optional[int] = None
    registration_number: Optional[str] = None
    inn: Optional[str] = None


# ========== УПРАВЛЕНИЕ СОЕДИНЕНИЕМ ==========

@router.post("/open")
async def open_connection(request: OpenConnectionRequest):
    """
    Открыть логическое соединение с ККТ (fptr.open)

    Устанавливает соединение с устройством на основе текущих настроек драйвера
    или настроек, переданных в запросе.

    Настройки подключения (примеры):

    TCP/IP:
    ```json
    {
        "Port": 2,
        "IPAddress": "192.168.1.100",
        "IPPort": 5555
    }
    ```

    COM/Serial:
    ```json
    {
        "Port": 1,
        "ComFile": "/dev/ttyUSB0",
        "BaudRate": 115200
    }
    ```

    USB:
    ```json
    {
        "Port": 0
    }
    ```

    Bluetooth:
    ```json
    {
        "Port": 3,
        "MACAddress": "00:11:22:33:44:55"
    }
    ```

    Типы подключения (Port):
    - 0: USB (LIBFPTR_PORT_USB)
    - 1: COM/Serial (LIBFPTR_PORT_COM)
    - 2: TCP/IP (LIBFPTR_PORT_TCPIP)
    - 3: Bluetooth (LIBFPTR_PORT_BLUETOOTH)
    """
    check_driver()

    try:
        # Если переданы настройки, применяем их
        if request.settings:
            driver.fptr.setSettings(request.settings)

        # Открываем соединение
        result = driver.fptr.open()

        if result < 0:
            error_code = driver.fptr.errorCode()
            error_desc = driver.fptr.errorDescription()
            raise AtolDriverError(f"Ошибка открытия соединения [код {error_code}]: {error_desc}")

        return StatusResponse(
            success=True,
            message="Соединение с ККТ успешно установлено"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/close")
async def close_connection():
    """
    Закрыть логическое соединение с ККТ (fptr.close)

    Закрывает активное соединение с устройством.
    После закрытия необходимо вызвать open для повторного подключения.
    """
    check_driver()

    try:
        result = driver.fptr.close()

        if result < 0:
            raise AtolDriverError(f"Ошибка закрытия соединения: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Соединение с ККТ закрыто"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/is-opened", response_model=ConnectionStatusResponse)
async def is_connection_opened():
    """
    Проверить состояние логического соединения (fptr.isOpened)

    Возвращает true если соединение с устройством активно, false если нет.
    """
    check_driver()

    try:
        is_opened = driver.fptr.isOpened()

        return ConnectionStatusResponse(
            is_opened=is_opened,
            message="Соединение активно" if is_opened else "Соединение не установлено"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ==========

@router.get("/settings")
async def get_connection_settings():
    """
    Получить текущие настройки подключения (fptr.getSettings)

    Возвращает все настройки драйвера в виде словаря.
    """
    check_driver()

    try:
        settings = driver.fptr.getSettings()
        return {"settings": settings}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/settings")
async def set_connection_settings(settings: Dict[str, Any]):
    """
    Установить настройки подключения (fptr.setSettings)

    Устанавливает настройки драйвера без установки соединения.
    Соединение устанавливается при вызове /connection/open.

    Args:
        settings: Словарь с настройками (см. описание в /connection/open)
    """
    check_driver()

    try:
        driver.fptr.setSettings(settings)

        return StatusResponse(
            success=True,
            message="Настройки подключения обновлены"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/settings/{key}")
async def get_single_setting(key: str):
    """
    Получить значение одной настройки (fptr.getSingleSetting)

    Args:
        key: Ключ настройки (например: IPAddress, IPPort, ComFile, BaudRate)
    """
    check_driver()

    try:
        value = driver.fptr.getSingleSetting(key)
        return {"key": key, "value": value}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/settings/{key}")
async def set_single_setting(key: str, value: Any):
    """
    Установить значение одной настройки (fptr.setSingleSetting)

    Args:
        key: Ключ настройки
        value: Значение настройки
    """
    check_driver()

    try:
        driver.fptr.setSingleSetting(key, value)

        return StatusResponse(
            success=True,
            message=f"Настройка '{key}' обновлена"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ ==========

@router.get("/device-info", response_model=DeviceInfoResponse)
async def get_device_info():
    """
    Получить информацию о подключенном устройстве

    Запрашивает основные данные о ККТ:
    - Серийный номер
    - Модель
    - Версию прошивки
    - Номер ФН
    - Регистрационный номер
    - ИНН

    Требуется активное соединение с устройством.
    """
    check_driver()

    try:
        # Проверяем что соединение активно
        if not driver.fptr.isOpened():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Соединение с ККТ не установлено"
            )

        # Запрашиваем серийный номер
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SERIAL_NUMBER)
        driver.fptr.queryData()
        serial_number = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)

        # Запрашиваем модель
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_MODEL_INFO)
        driver.fptr.queryData()
        model_name = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)

        # Запрашиваем версию прошивки
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, 0)  # Прошивка
        driver.fptr.queryData()
        firmware_version = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)

        # Запрашиваем общий статус для ФН
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        driver.fptr.queryData()
        fn_number = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_STORAGE_NUMBER)
        fn_lifetime_state = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_LIFE_STATE)
        registration_number = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_REGISTRATION_NUMBER)
        inn = driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_INN)

        return DeviceInfoResponse(
            serial_number=serial_number,
            model_name=model_name,
            firmware_version=firmware_version,
            fn_number=fn_number,
            fn_lifetime_state=fn_lifetime_state,
            registration_number=registration_number,
            inn=inn
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СЛУЖЕБНЫЕ ОПЕРАЦИИ ==========

@router.post("/test")
async def test_connection():
    """
    Протестировать соединение с ККТ

    Отправляет тестовый запрос к устройству для проверки работоспособности связи.
    """
    check_driver()

    try:
        if not driver.fptr.isOpened():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Соединение с ККТ не установлено"
            )

        # Пробуем запросить короткий статус - быстрая операция
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHORT_STATUS)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Тест соединения не пройден: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Тест соединения успешно пройден"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
