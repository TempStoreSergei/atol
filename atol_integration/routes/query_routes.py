"""
REST API endpoint'ы для запросов информации от ККТ (queryData)

Использует QueryDataService для выполнения запросов без дублирования кода.
"""
from fastapi import APIRouter, HTTPException, status
from ..api.driver import AtolDriverError
from ..services.query_data import QueryDataService

router = APIRouter(prefix="/query", tags=["Query"])

# Глобальный экземпляр сервиса (будет установлен из server.py)
query_service: QueryDataService = None


def set_query_service(service: QueryDataService):
    """Установить экземпляр сервиса для использования в routes"""
    global query_service
    query_service = service


def check_service():
    """Проверить что сервис инициализирован"""
    if query_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query service not initialized"
        )


# ========== БАЗОВЫЕ ЗАПРОСЫ СТАТУСА ==========

@router.get("/status")
async def get_status():
    """
    Запрос общей информации и статуса ККТ (LIBFPTR_DT_STATUS)

    Возвращает полную информацию о состоянии ККТ.
    """
    check_service()
    try:
        return query_service.get_status()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/short-status")
async def get_short_status():
    """Короткий запрос статуса ККТ (LIBFPTR_DT_SHORT_STATUS)"""
    check_service()
    try:
        return query_service.get_short_status()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cash-sum")
async def get_cash_sum():
    """Запрос суммы наличных в денежном ящике (LIBFPTR_DT_CASH_SUM)"""
    check_service()
    try:
        return query_service.get_cash_sum()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/unit-version")
async def get_unit_version(unit_type: int):
    """
    Запрос версии модуля (LIBFPTR_DT_UNIT_VERSION)

    Args:
        unit_type:
            - 0: прошивка
            - 1: конфигурация
            - 2: движок шаблонов
            - 3: блок управления
            - 4: загрузчик
    """
    check_service()
    try:
        return query_service.get_unit_version(unit_type)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/shift-state")
async def get_shift_state():
    """Запрос состояния смены (LIBFPTR_DT_SHIFT_STATE)"""
    check_service()
    try:
        return query_service.get_shift_state()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/receipt-state")
async def get_receipt_state():
    """Запрос состояния чека (LIBFPTR_DT_RECEIPT_STATE)"""
    check_service()
    try:
        return query_service.get_receipt_state()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/serial-number")
async def get_serial_number():
    """Запрос заводского номера ККТ (LIBFPTR_DT_SERIAL_NUMBER)"""
    check_service()
    try:
        return query_service.get_serial_number()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/model-info")
async def get_model_info():
    """Запрос информации о модели ККТ (LIBFPTR_DT_MODEL_INFO)"""
    check_service()
    try:
        return query_service.get_model_info()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/date-time")
async def get_date_time():
    """Запрос текущих даты и времени ККТ (LIBFPTR_DT_DATE_TIME)"""
    check_service()
    try:
        return query_service.get_date_time()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/receipt-line-length")
async def get_receipt_line_length():
    """Запрос ширины чековой ленты (LIBFPTR_DT_RECEIPT_LINE_LENGTH)"""
    check_service()
    try:
        return query_service.get_receipt_line_length()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СЧЕТЧИКИ И СУММЫ ==========

@router.get("/payment-sum")
async def get_payment_sum(receipt_type: int, payment_type: int):
    """Запрос суммы платежей за смену (LIBFPTR_DT_PAYMENT_SUM)"""
    check_service()
    try:
        return query_service.get_payment_sum(receipt_type, payment_type)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cashin-sum")
async def get_cashin_sum():
    """Запрос суммы внесений (LIBFPTR_DT_CASHIN_SUM)"""
    check_service()
    try:
        return query_service.get_cashin_sum()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cashout-sum")
async def get_cashout_sum():
    """Запрос суммы выплат (LIBFPTR_DT_CASHOUT_SUM)"""
    check_service()
    try:
        return query_service.get_cashout_sum()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cashin-count")
async def get_cashin_count():
    """Запрос количества внесений (LIBFPTR_DT_CASHIN_COUNT)"""
    check_service()
    try:
        return query_service.get_cashin_count()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cashout-count")
async def get_cashout_count():
    """Запрос количества выплат (LIBFPTR_DT_CASHOUT_COUNT)"""
    check_service()
    try:
        return query_service.get_cashout_count()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/receipt-count")
async def get_receipt_count(receipt_type: int):
    """Запрос количества чеков (LIBFPTR_DT_RECEIPT_COUNT)"""
    check_service()
    try:
        return query_service.get_receipt_count(receipt_type)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СЕТЕВАЯ ИНФОРМАЦИЯ ==========

@router.get("/mac-address")
async def get_mac_address():
    """Запрос MAC-адреса Ethernet (LIBFPTR_DT_MAC_ADDRESS)"""
    check_service()
    try:
        return query_service.get_mac_address()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ethernet-info")
async def get_ethernet_info():
    """Запрос текущей конфигурации Ethernet (LIBFPTR_DT_ETHERNET_INFO)"""
    check_service()
    try:
        return query_service.get_ethernet_info()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/wifi-info")
async def get_wifi_info():
    """Запрос текущей конфигурации Wi-Fi (LIBFPTR_DT_WIFI_INFO)"""
    check_service()
    try:
        return query_service.get_wifi_info()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== АППАРАТНАЯ ИНФОРМАЦИЯ ==========

@router.get("/printer-temperature")
async def get_printer_temperature():
    """Запрос температуры ТПГ (LIBFPTR_DT_PRINTER_TEMPERATURE)"""
    check_service()
    try:
        return query_service.get_printer_temperature()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/power-source-state")
async def get_power_source_state(power_source_type: int):
    """
    Запрос состояния источника питания (LIBFPTR_DT_POWER_SOURCE_STATE)

    Args:
        power_source_type:
            - 0: внешний блок питания
            - 1: батарея часов
            - 2: встроенные аккумуляторы
    """
    check_service()
    try:
        return query_service.get_power_source_state(power_source_type)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/mcu-info")
async def get_mcu_info():
    """Запрос информации о микроконтроллере (LIBFPTR_DT_MCU_INFO)"""
    check_service()
    try:
        return query_service.get_mcu_info()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СПЕЦИФИЧНЫЕ ЗАПРОСЫ ==========

@router.get("/lk-user-code")
async def get_lk_user_code():
    """Запрос кода привязки к ЛК (LIBFPTR_DT_LK_USER_CODE)"""
    check_service()
    try:
        return query_service.get_lk_user_code()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/last-sent-ofd-document-datetime")
async def get_last_sent_ofd_document_datetime():
    """Запрос даты последней отправки в ОФД (LIBFPTR_DT_LAST_SENT_OFD_DOCUMENT_DATE_TIME)"""
    check_service()
    try:
        return query_service.get_last_sent_ofd_document_datetime()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/last-sent-ism-notice-datetime")
async def get_last_sent_ism_notice_datetime():
    """Запрос даты последней отправки в ИСМ (LIBFPTR_DT_LAST_SENT_ISM_NOTICE_DATE_TIME)"""
    check_service()
    try:
        return query_service.get_last_sent_ism_notice_datetime()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/scripts-info")
async def get_scripts_info():
    """Запрос информации о загруженном шаблоне (LIBFPTR_DT_SCRIPTS_INFO)"""
    check_service()
    try:
        return query_service.get_scripts_info()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/shift-totals")
async def get_shift_totals(receipt_type: int):
    """Запрос сменного итога (LIBFPTR_DT_SHIFT_TOTALS)"""
    check_service()
    try:
        return query_service.get_shift_totals(receipt_type)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/font-info")
async def get_font_info(font_number: int):
    """Запрос параметров шрифта (LIBFPTR_DT_FONT_INFO)"""
    check_service()
    try:
        return query_service.get_font_info(font_number)
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/softlock-status")
async def get_softlock_status():
    """Запрос состояния привязки к ПО (LIBFPTR_DT_SOFTLOCK_STATUS)"""
    check_service()
    try:
        return query_service.get_softlock_status()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/cache-requisites")
async def get_cache_requisites():
    """Запрос кэшированных реквизитов (LIBFPTR_DT_CACHE_REQUISITES)"""
    check_service()
    try:
        return query_service.get_cache_requisites()
    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
