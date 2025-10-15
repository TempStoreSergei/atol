"""
REST API endpoint'ы для запросов информации от ККТ (queryData)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..api.redis_client import RedisClient, get_redis_client
from ..api.libfptr10 import IFptr

router = APIRouter(prefix="/query", tags=["Device Information Query"])


# ========== БАЗОВЫЕ ЗАПРОСЫ СТАТУСА ==========

@router.get("/status")
async def get_status(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос полной информации и статуса ККТ.

    Возвращает: модель, серийный номер, состояние смены, крышка, наличие бумаги,
    заводской номер, версию ПО, оператор, фискальные флаги и многое другое.
    """
    return redis.execute_command('get_status')


@router.get("/short-status")
async def get_short_status(redis: RedisClient = Depends(get_redis_client)):
    """
    Короткий запрос статуса ККТ.

    Возвращает только: денежный ящик открыт, наличие бумаги, бумага заканчивается, крышка открыта.
    """
    return redis.execute_command('get_short_status')


@router.get("/cash-sum")
async def get_cash_sum(redis: RedisClient = Depends(get_redis_client)):
    """Запрос суммы наличных в денежном ящике."""
    return redis.execute_command('get_cash_sum')


@router.get("/shift-state")
async def get_shift_state(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос состояния смены.

    Возвращает: состояние смены (закрыта/открыта/истекла), номер смены, дата и время истечения.
    """
    return redis.execute_command('get_shift_state')


@router.get("/receipt-state")
async def get_receipt_state(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос состояния чека.

    Возвращает: тип чека, сумму чека, номер чека, номер документа, неоплаченный остаток, сдачу.
    """
    return redis.execute_command('get_receipt_state')


@router.get("/datetime")
async def get_datetime(redis: RedisClient = Depends(get_redis_client)):
    """Запрос текущих даты и времени в ККТ."""
    return redis.execute_command('get_datetime')


@router.get("/serial-number")
async def get_serial_number(redis: RedisClient = Depends(get_redis_client)):
    """Запрос заводского номера ККТ."""
    return redis.execute_command('get_serial_number')


@router.get("/model-info")
async def get_model_info(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос информации о модели ККТ.

    Возвращает: номер модели, название модели, версию ПО.
    """
    return redis.execute_command('get_model_info')


@router.get("/receipt-line-length")
async def get_receipt_line_length(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос ширины чековой ленты.

    Возвращает ширину в символах и пикселях.
    """
    return redis.execute_command('get_receipt_line_length')


# ========== ЗАПРОСЫ ВЕРСИЙ МОДУЛЕЙ ==========

@router.get("/unit-version")
async def get_unit_version(
    unit_type: int = Query(
        IFptr.LIBFPTR_UT_FIRMWARE,
        description=(
            "Тип модуля: 0=прошивка (FIRMWARE), 1=конфигурация (CONFIGURATION), "
            "2=шаблоны (TEMPLATES), 3=блок управления (CONTROL_UNIT), 4=загрузчик (BOOT)"
        )
    ),
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
    return redis.execute_command('get_unit_version', {'unit_type': unit_type})


# ========== СЧЕТЧИКИ И СУММЫ ==========

class PaymentSumRequest(BaseModel):
    """Параметры запроса суммы платежей"""
    payment_type: int = Query(..., description="Тип оплаты: 0=наличные, 1=безнал, 2=аванс, 3=кредит, 4=иное")
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат продажи, 2=покупка, 3=возврат покупки")


@router.get("/payment-sum")
async def get_payment_sum(
    payment_type: int = Query(..., description="Тип оплаты: 0=наличные, 1=безнал, 2=аванс, 3=кредит, 4=иное"),
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
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
    return redis.execute_command('get_payment_sum', {
        'payment_type': payment_type,
        'receipt_type': receipt_type
    })


@router.get("/cashin-sum")
async def get_cashin_sum(redis: RedisClient = Depends(get_redis_client)):
    """Запрос суммы внесений за смену."""
    return redis.execute_command('get_cashin_sum')


@router.get("/cashout-sum")
async def get_cashout_sum(redis: RedisClient = Depends(get_redis_client)):
    """Запрос суммы выплат за смену."""
    return redis.execute_command('get_cashout_sum')


@router.get("/receipt-count")
async def get_receipt_count(
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
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
    return redis.execute_command('get_receipt_count', {'receipt_type': receipt_type})


@router.get("/non-nullable-sum")
async def get_non_nullable_sum(
    receipt_type: int = Query(..., description="Тип чека: 0=продажа, 1=возврат, 2=покупка, 3=возврат покупки"),
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Запрос необнуляемой суммы по типу чека.

    Необнуляемая сумма - это накопительный итог с момента фискализации ККТ.
    """
    return redis.execute_command('get_non_nullable_sum', {'receipt_type': receipt_type})


# ========== ПИТАНИЕ И ТЕМПЕРАТУРА ==========

@router.get("/power-source-state")
async def get_power_source_state(
    power_source_type: int = Query(
        IFptr.LIBFPTR_PST_BATTERY,
        description="Тип источника: 0=блок питания, 1=батарея часов, 2=аккумуляторы"
    ),
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
    return redis.execute_command('get_power_source_state', {'power_source_type': power_source_type})


@router.get("/printer-temperature")
async def get_printer_temperature(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос температуры термопечатающей головки (ТПГ).

    Возвращает температуру в градусах Цельсия.
    """
    return redis.execute_command('get_printer_temperature')


# ========== ДИАГНОСТИКА И ОШИБКИ ==========

@router.get("/fatal-status")
async def get_fatal_status(redis: RedisClient = Depends(get_redis_client)):
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
    return redis.execute_command('get_fatal_status')


# ========== СЕТЕВЫЕ ИНТЕРФЕЙСЫ ==========

@router.get("/mac-address")
async def get_mac_address(redis: RedisClient = Depends(get_redis_client)):
    """Запрос MAC-адреса Ethernet."""
    return redis.execute_command('get_mac_address')


@router.get("/ethernet-info")
async def get_ethernet_info(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос текущей конфигурации Ethernet.

    Возвращает: IP-адрес, маска сети, шлюз, DNS, порт, таймаут, DHCP, статический DNS.

    Поддерживается только для ККТ версий 5.X.
    """
    return redis.execute_command('get_ethernet_info')


@router.get("/wifi-info")
async def get_wifi_info(redis: RedisClient = Depends(get_redis_client)):
    """
    Запрос текущей конфигурации Wi-Fi.

    Возвращает: IP-адрес, маска сети, шлюз, порт, таймаут, DHCP.

    Поддерживается только для ККТ версий 5.X.
    """
    return redis.execute_command('get_wifi_info')

