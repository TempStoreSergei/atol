"""
REST API endpoint'ы для запросов информации от ККТ (queryData)
"""
from typing import Optional
from fastapi import Depends, Query, status
from pydantic import BaseModel

from ..api.redis_client import RedisClient, get_redis_client
from ..api.libfptr10 import IFptr
from ..api.routing import RouteDTO, RouterFactory


# ========== МОДЕЛИ ДАННЫХ ==========

class StatusResponse(BaseModel):
    """Полная информация о статусе ККТ"""
    success: bool
    message: Optional[str] = None


class ShortStatusResponse(BaseModel):
    """Короткий статус ККТ"""
    drawer_opened: bool
    paper_present: bool
    paper_near_end: bool
    cover_opened: bool


class CashSumResponse(BaseModel):
    """Сумма наличных в денежном ящике"""
    cash_sum: float


class ShiftStateResponse(BaseModel):
    """Состояние смены"""
    state: int  # 0=закрыта, 1=открыта, 2=истекла
    shift_number: int
    expiration_datetime: Optional[str] = None


class ReceiptStateResponse(BaseModel):
    """Состояние чека"""
    receipt_type: int
    receipt_sum: float
    receipt_number: int
    document_number: int
    unpaid_sum: float
    change_sum: float


class DateTimeResponse(BaseModel):
    """Дата и время ККТ"""
    datetime: str


class SerialNumberResponse(BaseModel):
    """Заводской номер ККТ"""
    serial_number: str


class ModelInfoResponse(BaseModel):
    """Информация о модели ККТ"""
    model_number: int
    model_name: str
    firmware_version: str


class ReceiptLineLengthResponse(BaseModel):
    """Ширина чековой ленты"""
    line_length_chars: int
    line_length_pixels: int


class UnitVersionResponse(BaseModel):
    """Версия модуля ККТ"""
    version: str
    release_version: Optional[str] = None


class PaymentSumRequest(BaseModel):
    """Параметры запроса суммы платежей"""
    payment_type: int
    receipt_type: int


class PowerSourceStateResponse(BaseModel):
    """Состояние источника питания"""
    battery_charge_percent: Optional[int] = None
    voltage: Optional[float] = None
    is_battery_powered: bool
    is_charging: bool
    can_print: bool


class PrinterTemperatureResponse(BaseModel):
    """Температура печатающей головки"""
    temperature_celsius: float


class FatalStatusResponse(BaseModel):
    """Фатальные ошибки ККТ"""
    has_fatal_errors: bool
    errors: list[str] = []


class MacAddressResponse(BaseModel):
    """MAC-адрес Ethernet"""
    mac_address: str


class EthernetInfoResponse(BaseModel):
    """Конфигурация Ethernet"""
    ip_address: str
    subnet_mask: str
    gateway: str
    dns: str
    port: int
    timeout: int
    dhcp_enabled: bool
    static_dns: bool


class WiFiInfoResponse(BaseModel):
    """Конфигурация Wi-Fi"""
    ip_address: str
    subnet_mask: str
    gateway: str
    port: int
    timeout: int
    dhcp_enabled: bool


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def get_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос полной информации и статуса ККТ.

    Возвращает: модель, серийный номер, состояние смены, крышка, наличие бумаги,
    заводской номер, версию ПО, оператор, фискальные флаги и многое другое.
    """
    return redis.execute_command('get_status', device_id=device_id)


async def get_short_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Короткий запрос статуса ККТ.

    Возвращает только: денежный ящик открыт, наличие бумаги, бумага заканчивается, крышка открыта.
    """
    return redis.execute_command('get_short_status', device_id=device_id)


async def get_cash_sum(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос суммы наличных в денежном ящике."""
    return redis.execute_command('get_cash_sum', device_id=device_id)


async def get_shift_state(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос состояния смены.

    Возвращает: состояние смены (закрыта/открыта/истекла), номер смены, дата и время истечения.
    """
    return redis.execute_command('get_shift_state', device_id=device_id)


async def get_receipt_state(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос состояния чека.

    Возвращает: тип чека, сумму чека, номер чека, номер документа, неоплаченный остаток, сдачу.
    """
    return redis.execute_command('get_receipt_state', device_id=device_id)


async def get_datetime(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос текущих даты и времени в ККТ."""
    return redis.execute_command('get_datetime', device_id=device_id)


async def get_serial_number(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос заводского номера ККТ."""
    return redis.execute_command('get_serial_number', device_id=device_id)


async def get_model_info(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос информации о модели ККТ.

    Возвращает: номер модели, название модели, версию ПО.
    """
    return redis.execute_command('get_model_info', device_id=device_id)


async def get_receipt_line_length(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос ширины чековой ленты.

    Возвращает ширину в символах и пикселях.
    """
    return redis.execute_command('get_receipt_line_length', device_id=device_id)


async def get_unit_version(
    unit_type: int = Query(
        IFptr.LIBFPTR_UT_FIRMWARE,
        description=(
            "Тип модуля: 0=прошивка (FIRMWARE), 1=конфигурация (CONFIGURATION), "
            "2=шаблоны (TEMPLATES), 3=блок управления (CONTROL_UNIT), 4=загрузчик (BOOT)"
        )
    ),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос версии модуля ККТ.

    Типы модулей:
    - 0 (LIBFPTR_UT_FIRMWARE): Прошивка
    - 1 (LIBFPTR_UT_CONFIGURATION): Конфигурация (также возвращает версию релиза)
    - 2 (LIBFPTR_UT_TEMPLATES): Движок шаблонов
    - 3 (LIBFPTR_UT_CONTROL_UNIT): Блок управления
    - 4 (LIBFPTR_UT_BOOT): Загрузчик
    """
    return redis.execute_command('get_unit_version', device_id=device_id, kwargs={'unit_type': unit_type})


async def get_payment_sum(
    payment_type: int = Query(..., description="Тип оплаты: 0=наличные, 1=безнал, 2=аванс, 3=кредит, 4=иное"),
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос суммы платежей за смену по типу оплаты и типу чека.

    Типы оплаты (LIBFPTR_PARAM_PAYMENT_TYPE):
    - 0 = наличные (CASH)
    - 1 = безналичные (ELECTRONICALLY)
    - 2 = аванс (PREPAID)
    - 3 = кредит (CREDIT)
    - 4 = иное (OTHER)

    Типы чека (LIBFPTR_PARAM_RECEIPT_TYPE):
    - 0 = продажа (SELL)
    - 1 = возврат продажи (SELL_RETURN)
    - 2 = покупка (BUY)
    - 3 = возврат покупки (BUY_RETURN)
    """
    return redis.execute_command('get_payment_sum', device_id=device_id, kwargs={
        'payment_type': payment_type,
        'receipt_type': receipt_type
    })


async def get_cashin_sum(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос суммы внесений за смену."""
    return redis.execute_command('get_cashin_sum', device_id=device_id)


async def get_cashout_sum(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос суммы выплат за смену."""
    return redis.execute_command('get_cashout_sum', device_id=device_id)


async def get_receipt_count(
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос количества чеков за смену по типу.

    Типы чека (LIBFPTR_PARAM_RECEIPT_TYPE):
    - 0 = продажа (SELL)
    - 1 = возврат продажи (SELL_RETURN)
    - 2 = покупка (BUY)
    - 3 = возврат покупки (BUY_RETURN)
    - 4 = коррекция продажи (SELL_CORRECTION)
    - 5 = коррекция покупки (BUY_CORRECTION)
    """
    return redis.execute_command('get_receipt_count', device_id=device_id, kwargs={'receipt_type': receipt_type})


async def get_non_nullable_sum(
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос необнуляемой суммы по типу чека.

    Необнуляемая сумма - это накопительный итог с момента фискализации ККТ.
    """
    return redis.execute_command('get_non_nullable_sum', device_id=device_id, kwargs={'receipt_type': receipt_type})


async def get_power_source_state(
    power_source_type: int = Query(
        IFptr.LIBFPTR_PST_BATTERY,
        description="Тип источника: 0=блок питания, 1=батарея часов, 2=аккумуляторы"
    ),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос состояния источника питания.

    Типы источников (LIBFPTR_PARAM_POWER_SOURCE_TYPE):
    - 0 (LIBFPTR_PST_POWER_SUPPLY): Внешний блок питания
    - 1 (LIBFPTR_PST_RTC_BATTERY): Батарея часов
    - 2 (LIBFPTR_PST_BATTERY): Встроенные аккумуляторы (по умолчанию)

    Возвращает: заряд аккумулятора (%), напряжение (В), работа от аккумулятора,
    идет зарядка, может ли печатать при текущем заряде.
    """
    return redis.execute_command('get_power_source_state', device_id=device_id, kwargs={'power_source_type': power_source_type})


async def get_printer_temperature(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос температуры термопечатающей головки (ТПГ).

    Возвращает температуру в градусах Цельсия.
    """
    return redis.execute_command('get_printer_temperature', device_id=device_id)


async def get_fatal_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос фатальных ошибок ККТ.

    Возвращает флаги критических ошибок:
    - Отсутствие серийного номера
    - Сбой часов (RTC)
    - Сбой настроек
    - Сбой счетчиков
    - Сбой пользовательской памяти
    - Сбой сервисных регистров
    - Сбой реквизитов
    - Фатальная ошибка ФН
    - Установлен ФН из другой ККТ
    - Фатальная аппаратная ошибка
    - Ошибка диспетчера памяти
    - Шаблоны повреждены
    - Требуется перезагрузка
    - Ошибка универсальных счётчиков
    - Ошибка таблицы товаров
    """
    return redis.execute_command('get_fatal_status', device_id=device_id)


async def get_mac_address(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """Запрос MAC-адреса Ethernet."""
    return redis.execute_command('get_mac_address', device_id=device_id)


async def get_ethernet_info(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос текущей конфигурации Ethernet.

    Возвращает: IP-адрес, маска сети, шлюз, DNS, порт, таймаут, DHCP, статический DNS.

    Поддерживается только для ККТ версий 5.X.
    """
    return redis.execute_command('get_ethernet_info', device_id=device_id)


async def get_wifi_info(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос текущей конфигурации Wi-Fi.

    Возвращает: IP-адрес, маска сети, шлюз, порт, таймаут, DHCP.

    Поддерживается только для ККТ версий 5.X.
    """
    return redis.execute_command('get_wifi_info', device_id=device_id)


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

QUERY_ROUTES = [
    # БАЗОВЫЕ ЗАПРОСЫ СТАТУСА
    RouteDTO(
        path="/status",
        endpoint=get_status,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Полный статус ККТ",
        description="Запрос полной информации и статуса ККТ: модель, серийный номер, состояние смены, крышка, наличие бумаги и многое другое",
        responses={
            status.HTTP_200_OK: {
                "description": "Статус успешно получен",
            },
        },
    ),
    RouteDTO(
        path="/short-status",
        endpoint=get_short_status,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Короткий статус ККТ",
        description="Короткий запрос статуса: денежный ящик, бумага, крышка",
        responses={
            status.HTTP_200_OK: {
                "description": "Короткий статус получен",
            },
        },
    ),
    RouteDTO(
        path="/cash-sum",
        endpoint=get_cash_sum,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Сумма наличных",
        description="Запрос суммы наличных в денежном ящике",
        responses={
            status.HTTP_200_OK: {
                "description": "Сумма наличных получена",
            },
        },
    ),
    RouteDTO(
        path="/shift-state",
        endpoint=get_shift_state,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Состояние смены",
        description="Запрос состояния смены: состояние (закрыта/открыта/истекла), номер смены, дата истечения",
        responses={
            status.HTTP_200_OK: {
                "description": "Состояние смены получено",
            },
        },
    ),
    RouteDTO(
        path="/receipt-state",
        endpoint=get_receipt_state,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Состояние чека",
        description="Запрос состояния чека: тип, сумма, номер, неоплаченный остаток, сдача",
        responses={
            status.HTTP_200_OK: {
                "description": "Состояние чека получено",
            },
        },
    ),
    RouteDTO(
        path="/datetime",
        endpoint=get_datetime,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Дата и время",
        description="Запрос текущих даты и времени в ККТ",
        responses={
            status.HTTP_200_OK: {
                "description": "Дата и время получены",
            },
        },
    ),
    RouteDTO(
        path="/serial-number",
        endpoint=get_serial_number,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Заводской номер",
        description="Запрос заводского номера ККТ",
        responses={
            status.HTTP_200_OK: {
                "description": "Заводской номер получен",
            },
        },
    ),
    RouteDTO(
        path="/model-info",
        endpoint=get_model_info,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Информация о модели",
        description="Запрос информации о модели ККТ: номер модели, название, версия ПО",
        responses={
            status.HTTP_200_OK: {
                "description": "Информация о модели получена",
            },
        },
    ),
    RouteDTO(
        path="/receipt-line-length",
        endpoint=get_receipt_line_length,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Ширина чековой ленты",
        description="Запрос ширины чековой ленты в символах и пикселях",
        responses={
            status.HTTP_200_OK: {
                "description": "Ширина чековой ленты получена",
            },
        },
    ),

    # ЗАПРОСЫ ВЕРСИЙ МОДУЛЕЙ
    RouteDTO(
        path="/unit-version",
        endpoint=get_unit_version,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Версия модуля",
        description="Запрос версии модуля ККТ (прошивка, конфигурация, шаблоны, блок управления, загрузчик)",
        responses={
            status.HTTP_200_OK: {
                "description": "Версия модуля получена",
            },
        },
    ),

    # СЧЕТЧИКИ И СУММЫ
    RouteDTO(
        path="/payment-sum",
        endpoint=get_payment_sum,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Сумма платежей",
        description="Запрос суммы платежей за смену по типу оплаты и типу чека",
        responses={
            status.HTTP_200_OK: {
                "description": "Сумма платежей получена",
            },
        },
    ),
    RouteDTO(
        path="/cashin-sum",
        endpoint=get_cashin_sum,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Сумма внесений",
        description="Запрос суммы внесений за смену",
        responses={
            status.HTTP_200_OK: {
                "description": "Сумма внесений получена",
            },
        },
    ),
    RouteDTO(
        path="/cashout-sum",
        endpoint=get_cashout_sum,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Сумма выплат",
        description="Запрос суммы выплат за смену",
        responses={
            status.HTTP_200_OK: {
                "description": "Сумма выплат получена",
            },
        },
    ),
    RouteDTO(
        path="/receipt-count",
        endpoint=get_receipt_count,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Количество чеков",
        description="Запрос количества чеков за смену по типу",
        responses={
            status.HTTP_200_OK: {
                "description": "Количество чеков получено",
            },
        },
    ),
    RouteDTO(
        path="/non-nullable-sum",
        endpoint=get_non_nullable_sum,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Необнуляемая сумма",
        description="Запрос необнуляемой суммы (накопительный итог с момента фискализации) по типу чека",
        responses={
            status.HTTP_200_OK: {
                "description": "Необнуляемая сумма получена",
            },
        },
    ),

    # ПИТАНИЕ И ТЕМПЕРАТУРА
    RouteDTO(
        path="/power-source-state",
        endpoint=get_power_source_state,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Состояние питания",
        description="Запрос состояния источника питания: заряд, напряжение, работа от аккумулятора, зарядка",
        responses={
            status.HTTP_200_OK: {
                "description": "Состояние питания получено",
            },
        },
    ),
    RouteDTO(
        path="/printer-temperature",
        endpoint=get_printer_temperature,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Температура печатающей головки",
        description="Запрос температуры термопечатающей головки (ТПГ) в градусах Цельсия",
        responses={
            status.HTTP_200_OK: {
                "description": "Температура получена",
            },
        },
    ),

    # ДИАГНОСТИКА И ОШИБКИ
    RouteDTO(
        path="/fatal-status",
        endpoint=get_fatal_status,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Фатальные ошибки",
        description="Запрос фатальных ошибок ККТ: сбои оборудования, памяти, ФН и другие критические ошибки",
        responses={
            status.HTTP_200_OK: {
                "description": "Информация о фатальных ошибках получена",
            },
        },
    ),

    # СЕТЕВЫЕ ИНТЕРФЕЙСЫ
    RouteDTO(
        path="/mac-address",
        endpoint=get_mac_address,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="MAC-адрес",
        description="Запрос MAC-адреса Ethernet интерфейса",
        responses={
            status.HTTP_200_OK: {
                "description": "MAC-адрес получен",
            },
        },
    ),
    RouteDTO(
        path="/ethernet-info",
        endpoint=get_ethernet_info,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Конфигурация Ethernet",
        description="Запрос текущей конфигурации Ethernet: IP, маска, шлюз, DNS, порт (только для ККТ версий 5.X)",
        responses={
            status.HTTP_200_OK: {
                "description": "Конфигурация Ethernet получена",
            },
        },
    ),
    RouteDTO(
        path="/wifi-info",
        endpoint=get_wifi_info,
        response_model=None,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Конфигурация Wi-Fi",
        description="Запрос текущей конфигурации Wi-Fi: IP, маска, шлюз, порт (только для ККТ версий 5.X)",
        responses={
            status.HTTP_200_OK: {
                "description": "Конфигурация Wi-Fi получена",
            },
        },
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/query',
    tags=['Device Information Query'],
    routes=QUERY_ROUTES,
)
