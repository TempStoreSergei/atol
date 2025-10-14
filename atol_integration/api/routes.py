"""
FastAPI endpoints для работы с драйвером АТОЛ ККТ v.10
"""
from typing import Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from enum import IntEnum

from .driver import (
    AtolDriver,
    ConnectionType,
    ReceiptType,
    TaxType,
    PaymentType,
    AtolDriverError
)
from .errors import DriverErrorCode, get_error_message

# Глобальное хранилище драйверов (ключ - ID драйвера)
_drivers: Dict[str, AtolDriver] = {}

router = APIRouter(prefix="/api/v1/atol", tags=["ATOL Driver"])


# ==================== МОДЕЛИ ДАННЫХ ====================

class DriverInitRequest(BaseModel):
    """Запрос на инициализацию драйвера"""
    driver_id: str = Field(..., description="Уникальный идентификатор драйвера ([a-zA-Z0-9_-])")
    library_path: Optional[str] = Field(None, description="Путь к библиотеке драйвера")


class DriverInitResponse(BaseModel):
    """Ответ на инициализацию драйвера"""
    driver_id: str
    version: str
    message: str


class DriverSettingsRequest(BaseModel):
    """Запрос на настройку драйвера"""
    model: Optional[int] = Field(None, description="Модель ККТ")
    port: Optional[int] = Field(None, description="Тип подключения")
    access_password: Optional[str] = Field(None, description="Пароль доступа к ККТ")
    user_password: Optional[str] = Field(None, description="Пароль пользователя")
    # COM настройки
    com_file: Optional[str] = Field(None, description="COM порт или TTY файл")
    baudrate: Optional[int] = Field(None, description="Скорость обмена")
    bits: Optional[int] = Field(None, description="Количество бит")
    stopbits: Optional[int] = Field(None, description="Стоп-биты")
    parity: Optional[int] = Field(None, description="Четность")
    # USB настройки
    usb_device_path: Optional[str] = Field(None, description="Путь к USB устройству (Linux)")
    # TCP/IP настройки
    ip_address: Optional[str] = Field(None, description="IP адрес или hostname")
    ip_port: Optional[int] = Field(None, description="IP порт")
    # Bluetooth настройки
    mac_address: Optional[str] = Field(None, description="Bluetooth MAC адрес")
    # Дополнительные настройки
    auto_reconnect: Optional[bool] = Field(True, description="Автоматическое восстановление связи")
    ofd_channel: Optional[int] = Field(None, description="Канал обмена с ОФД")


class DriverSettingsResponse(BaseModel):
    """Ответ с текущими настройками драйвера"""
    settings: Dict[str, Any]


class ConnectionRequest(BaseModel):
    """Запрос на подключение к ККТ"""
    connection_type: int = Field(..., description="Тип подключения (0=USB, 1=SERIAL, 2=TCP, 3=BLUETOOTH)")
    host: Optional[str] = Field("localhost", description="IP адрес для TCP")
    port: Optional[int] = Field(5555, description="Порт для TCP")
    serial_port: Optional[str] = Field(None, description="COM порт для Serial")
    baudrate: Optional[int] = Field(115200, description="Скорость для Serial")


class ParameterSetRequest(BaseModel):
    """Запрос на установку параметра"""
    param_id: int = Field(..., description="ID параметра")
    value: Union[int, float, str, bool, list] = Field(..., description="Значение параметра")
    non_printable: bool = Field(False, description="Не печатать на чековой ленте (только ФН)")


class ParameterGetRequest(BaseModel):
    """Запрос на получение параметра"""
    param_id: int = Field(..., description="ID параметра")
    value_type: str = Field("int", description="Тип значения: int, float, str, bool, bytes, datetime")


class ParameterResponse(BaseModel):
    """Ответ с параметром"""
    param_id: int
    value: Any


class LabelRequest(BaseModel):
    """Запрос на изменение метки драйвера"""
    label: str = Field(..., description="Метка драйвера для логирования")


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_driver(driver_id: str) -> AtolDriver:
    """Получить драйвер по ID"""
    if driver_id not in _drivers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Драйвер с ID '{driver_id}' не найден"
        )
    return _drivers[driver_id]


# ==================== ENDPOINTS: ИНИЦИАЛИЗАЦИЯ ====================

@router.post("/driver/init", response_model=DriverInitResponse)
async def init_driver(request: DriverInitRequest):
    """
    Инициализация драйвера

    Создает новый экземпляр драйвера с указанным ID.
    ID может содержать только: a-zA-Z0-9_-
    """
    try:
        # Проверяем, не существует ли уже драйвер с таким ID
        if request.driver_id in _drivers:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Драйвер с ID '{request.driver_id}' уже существует"
            )

        # Создаём драйвер
        driver = AtolDriver()

        # Получаем версию драйвера
        version = driver.fptr.version() if driver.fptr else "unknown"

        # Сохраняем в хранилище
        _drivers[request.driver_id] = driver

        return DriverInitResponse(
            driver_id=request.driver_id,
            version=version,
            message="Драйвер успешно инициализирован"
        )

    except AtolDriverError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/driver/{driver_id}")
async def destroy_driver(driver_id: str):
    """
    Деинициализация драйвера

    Удаляет экземпляр драйвера и разрывает соединение с ККТ.
    """
    driver = get_driver(driver_id)

    try:
        driver.disconnect()
        del _drivers[driver_id]

        return StatusResponse(
            success=True,
            message=f"Драйвер '{driver_id}' успешно удалён"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/driver/{driver_id}/version")
async def get_driver_version(driver_id: str):
    """Получить версию драйвера"""
    driver = get_driver(driver_id)

    try:
        version = driver.fptr.version() if driver.fptr else "unknown"
        return {"version": version}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/driver/{driver_id}/label")
async def change_driver_label(driver_id: str, request: LabelRequest):
    """
    Изменить метку драйвера для логирования

    Метка добавляется в каждую строку лога (если в формате присутствует %L).
    Полезно при работе с несколькими экземплярами драйвера.
    """
    driver = get_driver(driver_id)

    try:
        driver.change_label(request.label)

        return StatusResponse(
            success=True,
            message=f"Метка драйвера изменена на '{request.label}'"
        )

    except AtolDriverError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== ENDPOINTS: НАСТРОЙКА ====================

@router.post("/driver/{driver_id}/settings", response_model=DriverSettingsResponse)
async def set_driver_settings(driver_id: str, request: DriverSettingsRequest):
    """
    Настроить драйвер

    Устанавливает настройки подключения к ККТ.
    При изменении настроек драйвер переподключается к устройству.
    """
    driver = get_driver(driver_id)

    try:
        settings = {}

        # Формируем словарь настроек из запроса
        if request.model is not None:
            settings["Model"] = request.model
        if request.port is not None:
            settings["Port"] = request.port
        if request.access_password:
            settings["AccessPassword"] = request.access_password
        if request.user_password:
            settings["UserPassword"] = request.user_password

        # COM настройки
        if request.com_file:
            settings["ComFile"] = request.com_file
        if request.baudrate is not None:
            settings["BaudRate"] = request.baudrate
        if request.bits is not None:
            settings["DataBits"] = request.bits
        if request.stopbits is not None:
            settings["StopBits"] = request.stopbits
        if request.parity is not None:
            settings["Parity"] = request.parity

        # USB настройки
        if request.usb_device_path:
            settings["UsbDevicePath"] = request.usb_device_path

        # TCP/IP настройки
        if request.ip_address:
            settings["IPAddress"] = request.ip_address
        if request.ip_port is not None:
            settings["IPPort"] = request.ip_port

        # Bluetooth настройки
        if request.mac_address:
            settings["MACAddress"] = request.mac_address

        # Дополнительные настройки
        if request.auto_reconnect is not None:
            settings["AutoReconnect"] = "1" if request.auto_reconnect else "0"
        if request.ofd_channel is not None:
            settings["OfdChannel"] = request.ofd_channel

        # Применяем настройки через драйвер
        driver.fptr.setSettings(settings)

        # Возвращаем текущие настройки
        current_settings = driver.fptr.getSettings()

        return DriverSettingsResponse(settings=current_settings)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/driver/{driver_id}/settings", response_model=DriverSettingsResponse)
async def get_driver_settings(driver_id: str):
    """
    Получить текущие настройки драйвера

    Возвращает все настройки в виде JSON.
    """
    driver = get_driver(driver_id)

    try:
        settings = driver.fptr.getSettings()
        return DriverSettingsResponse(settings=settings)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/driver/{driver_id}/settings/{setting_key}")
async def get_single_setting(driver_id: str, setting_key: str):
    """
    Получить отдельную настройку драйвера

    Возвращает значение конкретной настройки по ключу.
    """
    driver = get_driver(driver_id)

    try:
        value = driver.fptr.getSingleSetting(setting_key)
        return {"key": setting_key, "value": value}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== ENDPOINTS: ПОДКЛЮЧЕНИЕ ====================

@router.post("/driver/{driver_id}/connect")
async def connect_to_device(driver_id: str, request: ConnectionRequest):
    """
    Подключиться к ККТ

    Устанавливает соединение с кассовым аппаратом.
    """
    driver = get_driver(driver_id)

    try:
        driver.connect(
            connection_type=ConnectionType(request.connection_type),
            host=request.host,
            port=request.port,
            serial_port=request.serial_port,
            baudrate=request.baudrate
        )

        return StatusResponse(
            success=True,
            message="Успешно подключено к ККТ"
        )

    except AtolDriverError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/driver/{driver_id}/disconnect")
async def disconnect_from_device(driver_id: str):
    """
    Отключиться от ККТ

    Разрывает соединение с кассовым аппаратом.
    """
    driver = get_driver(driver_id)

    try:
        driver.disconnect()

        return StatusResponse(
            success=True,
            message="Отключено от ККТ"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/driver/{driver_id}/is_connected")
async def check_connection(driver_id: str):
    """
    Проверить подключение к ККТ

    Возвращает статус подключения.
    """
    driver = get_driver(driver_id)

    return {
        "connected": driver.is_connected()
    }


# ==================== ENDPOINTS: ПАРАМЕТРЫ ====================

@router.post("/driver/{driver_id}/param/set")
async def set_parameter(driver_id: str, request: ParameterSetRequest):
    """
    Установить параметр драйвера

    Устанавливает значение параметра или реквизита ФН.
    Поддерживает: int, float, str, bool, list (bytes).
    """
    driver = get_driver(driver_id)

    try:
        if request.non_printable:
            # Непечатаемый реквизит ФН
            driver.fptr.setNonPrintableParam(request.param_id, request.value)
        else:
            # Обычный параметр
            driver.set_param(request.param_id, request.value)

        return StatusResponse(
            success=True,
            message=f"Параметр {request.param_id} установлен"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/driver/{driver_id}/param/get", response_model=ParameterResponse)
async def get_parameter(driver_id: str, request: ParameterGetRequest):
    """
    Получить параметр драйвера

    Получает значение параметра указанного типа.
    Типы: int, float, str, bool, bytes, datetime
    """
    driver = get_driver(driver_id)

    try:
        value = None

        if request.value_type == "int":
            value = driver.fptr.getParamInt(request.param_id)
        elif request.value_type == "float":
            value = driver.fptr.getParamDouble(request.param_id)
        elif request.value_type == "str":
            value = driver.fptr.getParamString(request.param_id)
        elif request.value_type == "bool":
            value = driver.fptr.getParamBool(request.param_id)
        elif request.value_type == "bytes":
            value = driver.fptr.getParamByteArray(request.param_id)
        elif request.value_type == "datetime":
            value = driver.fptr.getParamDateTime(request.param_id)
            value = value.isoformat() if value else None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неизвестный тип значения: {request.value_type}"
            )

        return ParameterResponse(
            param_id=request.param_id,
            value=value
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== ENDPOINTS: ИНФОРМАЦИЯ ====================

@router.get("/drivers")
async def list_drivers():
    """
    Список всех активных драйверов

    Возвращает список ID всех инициализированных драйверов.
    """
    return {
        "drivers": list(_drivers.keys()),
        "count": len(_drivers)
    }


@router.get("/driver/{driver_id}/info")
async def get_device_info(driver_id: str):
    """
    Получить информацию об устройстве

    Возвращает информацию о подключенной ККТ.
    """
    driver = get_driver(driver_id)

    try:
        info = driver.get_device_info()
        return info

    except AtolDriverError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== ENDPOINTS: ОБРАБОТКА ОШИБОК ====================

@router.get("/driver/{driver_id}/error")
async def get_last_error(driver_id: str):
    """
    Получить последнюю ошибку драйвера

    Возвращает код и описание последней ошибки.
    Информация об ошибке сохраняется до следующего вызова метода драйвера.
    """
    driver = get_driver(driver_id)

    try:
        error_code = driver.fptr.errorCode()
        error_description = driver.fptr.errorDescription()

        return {
            "error_code": error_code,
            "error_description": error_description,
            "error_name": get_error_message(error_code) if error_code != 0 else "OK"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/driver/{driver_id}/error/reset")
async def reset_error(driver_id: str):
    """
    Сбросить информацию о последней ошибке

    Явно очищает информацию о последней ошибке драйвера.
    """
    driver = get_driver(driver_id)

    try:
        driver.fptr.resetError()

        return StatusResponse(
            success=True,
            message="Информация об ошибке сброшена"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/errors/codes")
async def list_error_codes():
    """
    Список всех кодов ошибок

    Возвращает полный список кодов ошибок драйвера с описаниями.
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
