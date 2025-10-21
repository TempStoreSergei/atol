"""
REST API endpoint'ы для операций с чеками (receipts)

Реализует полный функционал работы с чеками согласно документации ATOL Driver v.10:
- Открытие чека (продажа, возврат, коррекция)
- Регистрация позиций с поддержкой маркировки
- Регистрация оплат
- Регистрация налогов и итогов
- Закрытие и проверка чека
- Работа с кодами маркировки (ФФД 1.2)
"""
from typing import Optional, List, Dict, Any
from fastapi import Depends, Query, status, Body
from pydantic import BaseModel, Field

from ..api.dependencies import get_redis, pubsub_command_util
from redis.asyncio import Redis
from ..api.routing import RouteDTO, RouterFactory


# ========== КОНСТАНТЫ ==========

# Типы чеков (LIBFPTR_PARAM_RECEIPT_TYPE)
RECEIPT_TYPE_SELL = 0  # Чек прихода (продажи)
RECEIPT_TYPE_SELL_RETURN = 1  # Чек возврата прихода
RECEIPT_TYPE_SELL_CORRECTION = 2  # Чек коррекции прихода
RECEIPT_TYPE_SELL_RETURN_CORRECTION = 3  # Чек коррекции возврата прихода
RECEIPT_TYPE_BUY = 4  # Чек расхода (покупки)
RECEIPT_TYPE_BUY_RETURN = 5  # Чек возврата расхода
RECEIPT_TYPE_BUY_CORRECTION = 6  # Чек коррекции расхода
RECEIPT_TYPE_BUY_RETURN_CORRECTION = 7  # Чек коррекции возврата расхода

# Типы налогов (LIBFPTR_PARAM_TAX_TYPE)
TAX_VAT0 = 1  # НДС 0%
TAX_VAT10 = 2  # НДС 10%
TAX_VAT20 = 3  # НДС 20%
TAX_VAT110 = 4  # НДС рассчитанный 10/110
TAX_VAT120 = 5  # НДС рассчитанный 20/120
TAX_NO = 6  # Не облагается
TAX_VAT5 = 7  # НДС 5%
TAX_VAT105 = 8  # НДС рассчитанный 5/105
TAX_VAT7 = 9  # НДС 7%
TAX_VAT107 = 10  # НДС рассчитанный 7/107

# Способы расчета (LIBFPTR_PARAM_PAYMENT_TYPE)
PAYMENT_TYPE_CASH = 0  # Наличными
PAYMENT_TYPE_ELECTRONICALLY = 1  # Безналичными
PAYMENT_TYPE_PREPAID = 2  # Предварительная оплата (аванс)
PAYMENT_TYPE_CREDIT = 3  # Последующая оплата (кредит)
PAYMENT_TYPE_OTHER = 4  # Иная форма оплаты
PAYMENT_TYPE_6 = 5  # Способ расчета №6
PAYMENT_TYPE_7 = 6  # Способ расчета №7
PAYMENT_TYPE_8 = 7  # Способ расчета №8
PAYMENT_TYPE_9 = 8  # Способ расчета №9
PAYMENT_TYPE_10 = 9  # Способ расчета №10

# Системы налогообложения (тег 1055)
TAX_SYSTEM_OSN = 0  # Общая
TAX_SYSTEM_USN_INCOME = 1  # Упрощенная доход
TAX_SYSTEM_USN_INCOME_OUTCOME = 2  # Упрощенная доход минус расход
TAX_SYSTEM_ESN = 3  # Единый сельскохозяйственный доход
TAX_SYSTEM_PATENT = 4  # Патентная система налогообложения

# Типы агентов (тег 1057)
AGENT_TYPE_BANK_PAYING_AGENT = 0  # Банковский платежный агент
AGENT_TYPE_BANK_PAYING_SUBAGENT = 1  # Банковский платежный субагент
AGENT_TYPE_PAYING_AGENT = 2  # Платежный агент
AGENT_TYPE_PAYING_SUBAGENT = 3  # Платежный субагент
AGENT_TYPE_ATTORNEY = 4  # Поверенный
AGENT_TYPE_COMMISSION_AGENT = 5  # Комиссионер
AGENT_TYPE_ANOTHER = 6  # Другой тип агента

# Типы кодов маркировки (LIBFPTR_PARAM_MARKING_CODE_TYPE для ФФД 1.2)
MARKING_CODE_TYPE_AUTO = 0  # Определить автоматически
MARKING_CODE_TYPE_UNKNOWN = 1  # Неопознанный КМ
MARKING_CODE_TYPE_SHORT = 2  # Короткий КМ
MARKING_CODE_TYPE_88_CHECK = 3  # КМ 88 символов с проверкой в ФН
MARKING_CODE_TYPE_44_NO_CHECK = 4  # КМ 44 символа без проверки в ФН
MARKING_CODE_TYPE_44_CHECK = 5  # КМ 44 символа с проверкой в ФН
MARKING_CODE_TYPE_4_NO_CHECK = 6  # КМ 4 символа без проверки в ФН

# Статусы маркированных товаров (тег 2003, 2110)
MARKING_STATUS_PIECE_SOLD = 1  # Штучный товар, реализован
MARKING_STATUS_DRY_FOR_SALE = 2  # Мерный товар, в стадии реализации
MARKING_STATUS_PIECE_RETURN = 3  # Штучный товар, возвращен
MARKING_STATUS_DRY_RETURN = 4  # Часть товара, возвращена
MARKING_STATUS_PIECE_FOR_SALE = 5  # Штучный товар, в стадии реализации
MARKING_STATUS_DRY_SOLD = 6  # Мерный товар, реализован
MARKING_STATUS_UNCHANGED = 7  # Статус товара не изменился

# Единицы измерения (тег 2108)
MEASUREMENT_UNIT_PIECE = 0  # Штука
MEASUREMENT_UNIT_GRAM = 10  # Грамм
MEASUREMENT_UNIT_KILOGRAM = 11  # Килограмм
MEASUREMENT_UNIT_TON = 12  # Тонна
MEASUREMENT_UNIT_CENTIMETER = 20  # Сантиметр
MEASUREMENT_UNIT_METER = 21  # Метр
MEASUREMENT_UNIT_SQUARE_METER = 30  # Квадратный метр
MEASUREMENT_UNIT_LITER = 51  # Литр
MEASUREMENT_UNIT_CUBIC_METER = 70  # Кубический метр


# ========== МОДЕЛИ ДАННЫХ ==========

class OpenReceiptRequest(BaseModel):
    """Запрос на открытие чека"""
    receipt_type: int = Field(..., description="Тип чека (0-7, см. константы RECEIPT_TYPE_*)")
    electronically: bool = Field(False, description="Электронный чек (не печатать)")
    customer_contact: Optional[str] = Field(None, description="Email или телефон покупателя (тег 1008)")
    customer_name: Optional[str] = Field(None, description="Покупатель (клиент) (тег 1227, ФФД < 1.2)")
    customer_inn: Optional[str] = Field(None, description="ИНН покупателя (тег 1228)")
    email_sender: Optional[str] = Field(None, description="Email отправителя чека (тег 1117)")
    tax_system: Optional[int] = Field(None, description="Применяемая СНО (тег 1055, 0-4)")
    settlement_place: Optional[str] = Field(None, description="Место расчетов (тег 1187)")
    settlement_address: Optional[str] = Field(None, description="Адрес расчетов (тег 1009, ФФД ≥ 1.2)")
    fns_site: Optional[str] = Field(None, description="Адрес сайта ФНС (тег 1060)")
    agent_type: Optional[int] = Field(None, description="Признак агента (тег 1057, ФФД < 1.2, 0-6)")
    supplier_phone: Optional[str] = Field(None, description="Телефон поставщика (тег 1171, ФФД < 1.2)")
    bank_agent_operation: Optional[str] = Field(None, description="Операция банковского платежного агента (тег 1044)")
    payment_agent_phones: Optional[List[str]] = Field(None, description="Телефоны платежного агента (тег 1073)")
    transfer_operator_address: Optional[str] = Field(None, description="Адрес оператора перевода (тег 1005)")
    transfer_operator_inn: Optional[str] = Field(None, description="ИНН оператора перевода (тег 1016)")
    transfer_operator_name: Optional[str] = Field(None, description="Наименование оператора перевода (тег 1026)")
    transfer_operator_phones: Optional[List[str]] = Field(None, description="Телефоны оператора перевода (тег 1075)")
    payment_receiver_operator_phones: Optional[List[str]] = Field(None, description="Телефоны оператора по приему платежей (тег 1074)")
    user_attribute: Optional[bytes] = Field(None, description="Дополнительный реквизит пользователя (тег 1084)")
    receipt_additional_attribute: Optional[str] = Field(None, description="Дополнительный реквизит чека (БСО) (тег 1192)")
    client_info: Optional[bytes] = Field(None, description="Сведения о покупателе (тег 1256, ФФД ≥ 1.2)")
    industry_attribute: Optional[bytes] = Field(None, description="Отраслевой реквизит чека (тег 1261, ФФД ≥ 1.2)")
    operational_attribute: Optional[bytes] = Field(None, description="Операционный реквизит чека (тег 1270, ФФД ≥ 1.2)")
    internet_sign: bool = Field(False, description="Признак расчета в Интернет (тег 1125)")
    # Для чеков коррекции
    correction_type: Optional[int] = Field(None, description="Тип коррекции (тег 1173): 0=самостоятельно, 1=по предписанию")
    correction_base_date: Optional[str] = Field(None, description="Дата корректируемого расчета (тег 1178, формат YYYY-MM-DD)")
    correction_base_number: Optional[str] = Field(None, description="Номер предписания налогового органа (тег 1179)")


class CancelReceiptRequest(BaseModel):
    """Запрос на отмену чека"""
    clear_marking_table: bool = Field(True, description="Очистить внутреннюю таблицу КМ драйвера")


class RegistrationRequest(BaseModel):
    """Запрос на регистрацию позиции в чеке"""
    # Обязательные параметры
    name: str = Field(..., description="Наименование товара (LIBFPTR_PARAM_COMMODITY_NAME)")
    price: float = Field(..., description="Цена за единицу (LIBFPTR_PARAM_PRICE)")
    quantity: float = Field(1.0, description="Количество (LIBFPTR_PARAM_QUANTITY)")

    # Налогообложение
    tax_type: int = Field(TAX_NO, description="Тип НДС (LIBFPTR_PARAM_TAX_TYPE, 1-10)")
    tax_sum: Optional[float] = Field(None, description="Сумма налога (LIBFPTR_PARAM_TAX_SUM)")
    use_only_tax_type: bool = Field(False, description="Регистрировать только ставку налога без суммы")
    tax_mode: Optional[int] = Field(None, description="Способ начисления налога: 0=на позицию, 1=на единицу")

    # Дополнительные параметры позиции
    position_sum: Optional[float] = Field(None, description="Полная сумма позиции с учетом скидки/надбавки")
    department: Optional[int] = Field(None, description="Номер отдела (LIBFPTR_PARAM_DEPARTMENT)")
    info_discount_sum: Optional[float] = Field(None, description="Информация о скидке/надбавке")
    piece: bool = Field(False, description="Штучный товар (не печатать нули в дробной части)")
    check_sum: bool = Field(False, description="Проверять наличность в ДЯ при регистрации")

    # Фискальные реквизиты (ФФД)
    additional_attribute: Optional[str] = Field(None, description="Дополнительный реквизит предмета расчета (тег 1191)")
    measurement_unit_name: Optional[str] = Field(None, description="Единицы измерения предмета расчета (тег 1197, ФФД ≤ 1.1)")
    measurement_unit: Optional[int] = Field(None, description="Мера количества предмета расчета (тег 2108, ФФД ≥ 1.2)")
    payment_method_type: int = Field(4, description="Признак способа расчета (тег 1214)")
    payment_object_type: int = Field(1, description="Признак предмета расчета (тег 1212)")
    excise: Optional[float] = Field(None, description="Акциз (тег 1229)")
    country_code: Optional[str] = Field(None, description="Код страны происхождения товара (тег 1230)")
    customs_declaration: Optional[str] = Field(None, description="Номер таможенной декларации (тег 1231)")

    # Агенты и поставщики
    agent_type: Optional[int] = Field(None, description="Признак агента по предмету расчета (тег 1222)")
    agent_info: Optional[bytes] = Field(None, description="Данные агента (тег 1223)")
    supplier_info: Optional[bytes] = Field(None, description="Данные поставщика (тег 1224)")
    supplier_inn: Optional[str] = Field(None, description="ИНН поставщика (тег 1226)")

    # Коды товара (тег 1162 для ФФД ≤ 1.1)
    commodity_code: Optional[bytes] = Field(None, description="Код товара (тег 1162, ФФД ≤ 1.1)")

    # Коды товара (тег 1163 для ФФД ≥ 1.2) - автоопределение типа
    product_codes: Optional[List[str]] = Field(None, description="Коды товара без указания типа (LIBFPTR_PARAM_PRODUCT_CODE)")

    # Коды товара с указанием типа (теги 1300-1325)
    product_code_unknown: Optional[str] = Field(None, description="Нераспознанный код товара (тег 1300)")
    product_code_ean8: Optional[str] = Field(None, description="КТ EAN-8 (тег 1301)")
    product_code_ean13: Optional[str] = Field(None, description="КТ EAN-13 (тег 1302)")
    product_code_itf14: Optional[str] = Field(None, description="КТ ITF-14 (тег 1303)")
    product_code_gs10: Optional[str] = Field(None, description="КТ GS1.0 (тег 1304)")
    product_code_gs1m: Optional[str] = Field(None, description="КТ GS1.M (тег 1305)")
    product_code_short: Optional[str] = Field(None, description="КТ КМК короткий (тег 1306)")
    product_code_furs: Optional[str] = Field(None, description="КТ МИ меховые изделия (тег 1307)")
    product_code_egais20: Optional[str] = Field(None, description="КТ ЕГАИС-2.0 (тег 1308)")
    product_code_egais30: Optional[str] = Field(None, description="КТ ЕГАИС-3.0 (тег 1309)")

    # Маркировка (ФФД < 1.2)
    marking_code: Optional[str] = Field(None, description="Код маркировки (LIBFPTR_PARAM_MARKING_CODE)")
    marking_code_type: Optional[int] = Field(None, description="Тип кода маркировки: 0=ЕГАИС 2.0, 1=ЕГАИС 3.0, 2=другая")

    # Маркировка (ФФД ≥ 1.2)
    marking_code_ffd12: Optional[str] = Field(None, description="Код маркировки для ФФД 1.2 (тег 2000)")
    marking_code_status: Optional[int] = Field(None, description="Присвоенный статус товара (тег 2110)")
    marking_processing_mode: Optional[int] = Field(None, description="Режим обработки КМ (тег 2102)")
    marking_code_online_validation_result: Optional[int] = Field(None, description="Результат проверки сведений о товаре (тег 2106)")
    marking_product_id: Optional[str] = Field(None, description="Идентификатор товара (тег 2101)")
    marking_fractional_quantity: Optional[str] = Field(None, description="Дробное количество маркированного товара (формат '1/2')")

    # Отраслевой реквизит (тег 1260, ФФД ≥ 1.2)
    industry_attribute: Optional[bytes] = Field(None, description="Отраслевой реквизит предмета расчета (тег 1260)")


class PaymentRequest(BaseModel):
    """Запрос на регистрацию оплаты"""
    payment_type: int = Field(..., description="Способ расчета (0-9, см. PAYMENT_TYPE_*)")
    sum: float = Field(..., description="Сумма расчета (LIBFPTR_PARAM_PAYMENT_SUM)")

    # Сведения об оплате безналичными (тег 1235)
    electronically_payment_method: Optional[int] = Field(None, description="Признак способа оплаты безналичными (тег 1236)")
    electronically_id: Optional[str] = Field(None, description="Идентификатор безналичной оплаты (тег 1237)")
    electronically_add_info: Optional[str] = Field(None, description="Дополнительные сведения о безналичной оплате (тег 1238)")


class ReceiptTaxRequest(BaseModel):
    """Запрос на регистрацию налога на чек"""
    tax_type: int = Field(..., description="Тип налога (1-10, см. TAX_*)")
    tax_sum: float = Field(..., description="Сумма налога (LIBFPTR_PARAM_TAX_SUM)")


class ReceiptTotalRequest(BaseModel):
    """Запрос на регистрацию итога чека"""
    sum: float = Field(..., description="Сумма чека (LIBFPTR_PARAM_SUM)")


class CloseReceiptRequest(BaseModel):
    """Запрос на закрытие чека"""
    payment_type: Optional[int] = Field(None, description="Способ автооплаты неоплаченного остатка (по умолчанию 0=наличные)")


class WriteSalesNoticeRequest(BaseModel):
    """Запрос на передачу данных уведомления о реализации маркированного товара"""
    customer_inn: Optional[str] = Field(None, description="ИНН клиента (тег 1228)")
    industry_attributes: Optional[List[bytes]] = Field(None, description="Отраслевые реквизиты чека (тег 1261, можно несколько)")
    time_zone: Optional[int] = Field(None, description="Часовая зона (тег 1011)")


class BeginMarkingCodeValidationRequest(BaseModel):
    """Запрос на начало проверки кода маркировки"""
    marking_code: str = Field(..., description="Код маркировки (тег 2000)")
    marking_code_type: int = Field(MARKING_CODE_TYPE_AUTO, description="Тип КМ (тег 2100, 0-6)")
    marking_code_status: int = Field(..., description="Планируемый статус КМ (тег 2003, 1-7)")
    quantity: Optional[float] = Field(None, description="Количество товара (тег 1023)")
    measurement_unit: Optional[int] = Field(None, description="Мера количества товара (тег 2108)")
    marking_processing_mode: int = Field(0, description="Режим обработки кода товара (тег 2102)")
    marking_fractional_quantity: Optional[str] = Field(None, description="Дробное количество товара (тег 1292, формат '1/2')")
    timeout: int = Field(0, description="Таймаут ожидания проверки в мс (0=асинхронный режим)")
    not_send_to_server: bool = Field(False, description="Не отправлять запрос на сервер")
    not_form_request: bool = Field(False, description="Не формировать запрос")


# ========== ОТВЕТЫ ==========

class OpenReceiptResponse(BaseModel):
    """Ответ на открытие чека"""
    success: bool
    shift_auto_opened: Optional[bool] = Field(None, description="Смена открыта автоматически")
    receipt_size: Optional[int] = Field(None, description="Приблизительный размер чека в байтах")
    receipt_percentage_size: Optional[int] = Field(None, description="Размер чека в % от максимального (30 Кб)")


class RegistrationResponse(BaseModel):
    """Ответ на регистрацию позиции"""
    success: bool
    commodity_code: Optional[bytes] = Field(None, description="Значение тега 1162, если был передан MARKING_CODE")
    receipt_size: Optional[int] = None
    receipt_percentage_size: Optional[int] = None


class PaymentResponse(BaseModel):
    """Ответ на регистрацию оплаты"""
    success: bool
    remainder: Optional[float] = Field(None, description="Неоплаченный остаток чека")
    change: Optional[float] = Field(None, description="Сдача по чеку")


class CloseReceiptResponse(BaseModel):
    """Ответ на закрытие чека"""
    success: bool
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None


class CheckDocumentClosedResponse(BaseModel):
    """Ответ на проверку закрытия документа"""
    success: bool
    document_closed: bool = Field(..., description="Документ закрылся")
    document_printed: bool = Field(..., description="Документ допечатался")


class MarkingCodeValidationStatusResponse(BaseModel):
    """Ответ на получение статуса проверки КМ"""
    success: bool
    validation_ready: bool = Field(..., description="Проверка завершена")
    is_request_sent: Optional[bool] = Field(None, description="КМ был отправлен на сервер")
    online_validation_result: Optional[int] = Field(None, description="Результат проверки сведений о товаре (тег 2106)")
    online_validation_error: Optional[int] = Field(None, description="Ошибка онлайн проверки")
    online_validation_error_description: Optional[str] = Field(None, description="Описание ошибки онлайн проверки")
    tlv_list: Optional[str] = Field(None, description="Список полученных TLV-реквизитов")
    product_status_info: Optional[int] = Field(None, description="Сведения о статусе товара (тег 2109)")
    processing_result: Optional[int] = Field(None, description="Результаты обработки запроса (тег 2005)")
    processing_code: Optional[int] = Field(None, description="Код обработки запроса (тег 2105)")
    marking_code_type: Optional[int] = Field(None, description="Тип кода маркировки (тег 2100)")
    product_id: Optional[str] = Field(None, description="Идентификатор товара (тег 2101)")
    marking_processing_mode: Optional[int] = Field(None, description="Режим обработки КМ (тег 2102)")


class AcceptMarkingCodeResponse(BaseModel):
    """Ответ на подтверждение реализации товара"""
    success: bool
    online_validation_result: Optional[int] = Field(None, description="Результат проверки сведений о товаре (тег 2106)")


class MarkingServerStatusResponse(BaseModel):
    """Ответ на проверку сервера ИСМ"""
    success: bool
    check_ready: bool = Field(..., description="Проверка завершена")
    server_error_code: Optional[int] = Field(None, description="Ошибка проверки")
    server_error_description: Optional[str] = Field(None, description="Описание ошибки")
    response_time: Optional[int] = Field(None, description="Время ожидания ответа от сервера, мс")


class StatusResponse(BaseModel):
    """Общий статус операции"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ========== ФУНКЦИИ ЭНДПОИНТОВ ==========

async def open_receipt(
    request: OpenReceiptRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Открыть новый чек.

    Поддерживает все типы чеков:
    - Продажа (0), возврат продажи (1)
    - Покупка (4), возврат покупки (5)
    - Коррекция прихода (2), коррекция возврата прихода (3)
    - Коррекция расхода (6), коррекция возврата расхода (7)

    Для чеков коррекции обязательны параметры correction_type, correction_base_date, correction_base_number.
    """
    command = {
        "device_id": device_id,
        "command": "open_receipt",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def cancel_receipt(
    request: CancelReceiptRequest = Body(default=CancelReceiptRequest()),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Отменить открытый чек.

    Параметр clear_marking_table позволяет не очищать таблицу КМ драйвера,
    если планируется сразу провести точно такой же чек.
    """
    command = {
        "device_id": device_id,
        "command": "cancel_receipt",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def registration(
    request: RegistrationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Зарегистрировать позицию в чеке.

    Поддерживает:
    - Простые позиции с НДС
    - Позиции с маркировкой (ФФД < 1.2 и ФФД ≥ 1.2)
    - Позиции с агентами и поставщиками
    - Позиции с кодами товара (тег 1163)
    - Позиции с отраслевым реквизитом (тег 1260)
    """
    command = {
        "device_id": device_id,
        "command": "registration",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def payment(
    request: PaymentRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Зарегистрировать оплату чека.

    Поддерживаемые способы оплаты:
    - Наличными (0)
    - Безналичными (1) - с возможностью передачи дополнительных сведений
    - Предварительная оплата/аванс (2)
    - Последующая оплата/кредит (3)
    - Иная форма оплаты (4)
    - Способы расчета №6-10 (5-9)

    Для безналичной оплаты можно передать дополнительные сведения через
    параметры electronically_*.
    """
    command = {
        "device_id": device_id,
        "command": "payment",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def receipt_tax(
    request: ReceiptTaxRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Зарегистрировать налог на чек.

    Используется когда при регистрации позиций был установлен параметр
    use_only_tax_type=true.
    """
    command = {
        "device_id": device_id,
        "command": "receipt_tax",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def receipt_total(
    request: ReceiptTotalRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Зарегистрировать итог чека.

    Необязательный метод. Если не вызвать, сумма чека будет посчитана автоматически.
    Можно зарегистрировать итог с округлением в пределах ±99 копеек.
    """
    command = {
        "device_id": device_id,
        "command": "receipt_total",
        "kwargs": request.model_dump()
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def close_receipt(
    request: CloseReceiptRequest = Body(default=CloseReceiptRequest()),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Закрыть чек.

    Если чек не полностью оплачен, будет автоматически доплачен указанным
    способом оплаты (по умолчанию наличными).

    ВАЖНО: После закрытия чека обязательно вызовите check_document_closed()
    для проверки успешности операции!
    """
    command = {
        "device_id": device_id,
        "command": "close_receipt",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def check_document_closed(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Проверить закрытие документа.

    КРИТИЧЕСКИ ВАЖНЫЙ метод! Проверяет:
    - Закрылся ли документ в ФН
    - Напечатался ли документ на чековой ленте

    Если документ закрылся, но не напечатался - вызовите continue_print().
    Если документ не закрылся - отмените чек и сформируйте заново.

    Если метод вернул ошибку - нельзя выключать ПК, нужно восстановить работу ККТ!
    """
    command = {
        "device_id": device_id,
        "command": "check_document_closed"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def continue_print(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Допечатать фискальный документ.

    Используется когда документ закрылся в ФН, но не напечатался
    на чековой ленте (например, закончилась бумага).
    """
    command = {
        "device_id": device_id,
        "command": "continue_print"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


# ========== ОПЕРАЦИИ С КОДАМИ МАРКИРОВКИ (ФФД 1.2) ==========

async def begin_marking_code_validation(
    request: BeginMarkingCodeValidationRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Начать проверку кода маркировки.

    Режимы работы:
    - Асинхронный (timeout=0): метод не блокируется, нужно опрашивать статус через get_marking_code_validation_status()
    - Синхронный (timeout>0): метод блокируется до завершения проверки или таймаута

    После успешной проверки нужно вызвать:
    - accept_marking_code() для подтверждения реализации
    - decline_marking_code() для отказа от реализации
    - cancel_marking_code_validation() для отмены проверки
    """
    command = {
        "device_id": device_id,
        "command": "begin_marking_code_validation",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def get_marking_code_validation_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Получить статус проверки кода маркировки.

    В асинхронном режиме: вызывать до тех пор, пока validation_ready не станет true.
    В синхронном режиме: вызвать один раз для получения результата.
    """
    command = {
        "device_id": device_id,
        "command": "get_marking_code_validation_status"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def accept_marking_code(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Подтвердить реализацию товара с кодом маркировки.

    Вызывается после успешной проверки КМ.
    """
    command = {
        "device_id": device_id,
        "command": "accept_marking_code"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def decline_marking_code(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Отказаться от реализации товара с кодом маркировки.

    Вызывается после проверки КМ, если товар не будет реализован.
    """
    command = {
        "device_id": device_id,
        "command": "decline_marking_code"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def cancel_marking_code_validation(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Отменить проверку кода маркировки.

    Можно вызвать на любом этапе проверки для немедленной отмены.
    """
    command = {
        "device_id": device_id,
        "command": "cancel_marking_code_validation"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def clear_marking_code_validation_result(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Очистить таблицу проверенных кодов маркировки в ФН.
    """
    command = {
        "device_id": device_id,
        "command": "clear_marking_code_validation_result"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def check_marking_code_validations_ready(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Проверить завершение всех фоновых проверок КМ.

    Вызывается перед закрытием чека, если были запущены проверки КМ
    без ожидания результата.
    """
    command = {
        "device_id": device_id,
        "command": "check_marking_code_validations_ready"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def write_sales_notice(
    request: WriteSalesNoticeRequest,
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Передать данные уведомления о реализации маркированного товара.

    Условия вызова:
    - В чеке должны быть позиции с КМ
    - Вызывать только после регистрации всех позиций
    - Вызывать только до регистрации оплаты, налога, итога или закрытия чека

    Можно передать:
    - ИНН клиента (тег 1228)
    - Отраслевые реквизиты чека (тег 1261, можно несколько)
    - Часовую зону (тег 1011) - ОБЯЗАТЕЛЬНО для маркированных товаров!
    """
    command = {
        "device_id": device_id,
        "command": "write_sales_notice",
        "kwargs": request.model_dump(exclude_none=True)
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def update_fnm_keys(
    timeout: int = Query(60000, description="Таймаут ожидания обновления в мс"),
    print_report: bool = Query(False, description="Печать отчёта ОКП"),
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Обновить ключи проверки ФН-М.

    Метод блокирующий, выполняется до полного обновления ключей или таймаута.
    Поддерживается только для ККТ версий 5.X, работающих по ФФД ≥ 1.2.
    """
    command = {
        "device_id": device_id,
        "command": "update_fnm_keys",
        "kwargs": {
            "timeout": timeout,
            "print_update_fnm_keys_report": print_report
        }
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def ping_marking_server(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Начать проверку связи с сервером ИСМ.

    После вызова нужно опрашивать get_marking_server_status() до завершения проверки.
    Поддерживается только для ККТ версий 5.X, работающих по ФФД ≥ 1.2.
    """
    command = {
        "device_id": device_id,
        "command": "ping_marking_server"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


async def get_marking_server_status(
    device_id: str = Query("default", description="Идентификатор фискального регистратора"),
    redis: Redis = Depends(get_redis)
):
    """
    Получить статус проверки сервера ИСМ.

    Вызывать до тех пор, пока check_ready не станет true.
    """
    command = {
        "device_id": device_id,
        "command": "get_marking_server_status"
    }
    return await pubsub_command_util(redis, f"command_fr_channel_{device_id}", command)


# ========== ОПИСАНИЕ МАРШРУТОВ ==========

RECEIPT_ROUTES = [
    # Базовые операции с чеками
    RouteDTO(
        path="/open",
        endpoint=open_receipt,
        response_model=OpenReceiptResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Открыть чек",
        description="Открыть новый чек (продажа, возврат, покупка, коррекция)",
    ),
    RouteDTO(
        path="/cancel",
        endpoint=cancel_receipt,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Отменить чек",
        description="Отменить открытый чек без печати",
    ),
    RouteDTO(
        path="/registration",
        endpoint=registration,
        response_model=RegistrationResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Зарегистрировать позицию",
        description="Добавить товар/услугу в открытый чек",
    ),
    RouteDTO(
        path="/payment",
        endpoint=payment,
        response_model=PaymentResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Зарегистрировать оплату",
        description="Добавить оплату в открытый чек",
    ),
    RouteDTO(
        path="/tax",
        endpoint=receipt_tax,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Зарегистрировать налог на чек",
        description="Зарегистрировать сумму налога на чек",
    ),
    RouteDTO(
        path="/total",
        endpoint=receipt_total,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Зарегистрировать итог",
        description="Зарегистрировать итоговую сумму чека (необязательно)",
    ),
    RouteDTO(
        path="/close",
        endpoint=close_receipt,
        response_model=CloseReceiptResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Закрыть чек",
        description="Закрыть и напечатать чек",
    ),
    RouteDTO(
        path="/check-closed",
        endpoint=check_document_closed,
        response_model=CheckDocumentClosedResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Проверить закрытие чека",
        description="ВАЖНО! Проверить, что чек успешно закрылся и напечатался",
    ),
    RouteDTO(
        path="/continue-print",
        endpoint=continue_print,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Допечатать документ",
        description="Допечатать чек, если он закрылся, но не напечатался",
    ),

    # Операции с кодами маркировки (ФФД 1.2)
    RouteDTO(
        path="/marking/begin-validation",
        endpoint=begin_marking_code_validation,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Начать проверку КМ",
        description="Начать проверку кода маркировки (синхронный/асинхронный режим)",
    ),
    RouteDTO(
        path="/marking/validation-status",
        endpoint=get_marking_code_validation_status,
        response_model=MarkingCodeValidationStatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Статус проверки КМ",
        description="Получить статус проверки кода маркировки",
    ),
    RouteDTO(
        path="/marking/accept",
        endpoint=accept_marking_code,
        response_model=AcceptMarkingCodeResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Подтвердить реализацию КМ",
        description="Подтвердить реализацию товара с кодом маркировки",
    ),
    RouteDTO(
        path="/marking/decline",
        endpoint=decline_marking_code,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Отказаться от реализации КМ",
        description="Отказаться от реализации товара с кодом маркировки",
    ),
    RouteDTO(
        path="/marking/cancel-validation",
        endpoint=cancel_marking_code_validation,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Отменить проверку КМ",
        description="Отменить текущую проверку кода маркировки",
    ),
    RouteDTO(
        path="/marking/clear-validation-result",
        endpoint=clear_marking_code_validation_result,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Очистить таблицу КМ",
        description="Очистить таблицу проверенных кодов маркировки в ФН",
    ),
    RouteDTO(
        path="/marking/check-validations-ready",
        endpoint=check_marking_code_validations_ready,
        response_model=StatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Проверить готовность КМ",
        description="Проверить завершение всех фоновых проверок КМ",
    ),
    RouteDTO(
        path="/sales-notice",
        endpoint=write_sales_notice,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Передать данные уведомления",
        description="Передать данные уведомления о реализации маркированного товара",
    ),
    RouteDTO(
        path="/marking/update-fnm-keys",
        endpoint=update_fnm_keys,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Обновить ключи ФН-М",
        description="Обновить ключи проверки ФН-М (только ККТ 5.X, ФФД ≥ 1.2)",
    ),
    RouteDTO(
        path="/marking/ping-server",
        endpoint=ping_marking_server,
        response_model=StatusResponse,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        summary="Проверить сервер ИСМ",
        description="Начать проверку связи с сервером ИСМ",
    ),
    RouteDTO(
        path="/marking/server-status",
        endpoint=get_marking_server_status,
        response_model=MarkingServerStatusResponse,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        summary="Статус сервера ИСМ",
        description="Получить статус проверки сервера ИСМ",
    ),
]


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРА ==========

router = RouterFactory(
    prefix='/receipt',
    tags=['Receipt Operations'],
    routes=RECEIPT_ROUTES,
)
