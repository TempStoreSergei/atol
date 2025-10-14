"""
REST API endpoint'ы для операций с чеками (receipts)
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..api.driver import AtolDriver, AtolDriverError, ReceiptType, TaxType, PaymentType
from ..api import libfptr10
IFptr = libfptr10.IFptr

router = APIRouter(prefix="/receipt", tags=["Receipt"])

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

class OpenReceiptRequest(BaseModel):
    """Запрос на открытие чека"""
    receipt_type: int = Field(..., description="Тип чека (0=продажа, 1=возврат продажи, 2=покупка, 3=возврат покупки)")
    cashier_name: str = Field(..., description="Имя кассира")
    customer_contact: Optional[str] = Field(None, description="Email или телефон клиента")


class AddItemRequest(BaseModel):
    """Запрос на добавление позиции в чек"""
    name: str = Field(..., description="Наименование товара/услуги")
    price: float = Field(..., description="Цена за единицу")
    quantity: float = Field(1.0, description="Количество")
    tax_type: int = Field(TaxType.NONE.value, description="Тип НДС (0=без НДС, 1=0%, 2=10%, 3=20%, 4=10/110, 5=20/120)")
    payment_method: int = Field(4, description="Признак способа расчета (1-7)")
    payment_object: int = Field(1, description="Признак предмета расчета (1-13)")
    department: int = Field(0, description="Номер отдела (секции)")
    measure_unit: str = Field("шт", description="Единица измерения")


class AddPaymentRequest(BaseModel):
    """Запрос на добавление оплаты"""
    amount: float = Field(..., description="Сумма оплаты")
    payment_type: int = Field(PaymentType.CASH.value, description="Тип оплаты (0=наличные, 1=электронные, 2=предоплата, 3=кредит, 4=прочее)")


class CloseReceiptResponse(BaseModel):
    """Ответ на закрытие чека с фискальными данными"""
    success: bool
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    fiscal_storage_number: Optional[str] = None
    shift_number: Optional[int] = None
    receipt_number: Optional[int] = None
    fiscal_document_datetime: Optional[str] = None
    kkt_number: Optional[str] = None
    ofd_name: Optional[str] = None
    ofd_inn: Optional[str] = None
    ofd_site: Optional[str] = None
    ffd_version: Optional[int] = None
    fn_life_state: Optional[int] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ОСНОВНЫЕ ОПЕРАЦИИ С ЧЕКАМИ ==========

@router.post("/open")
async def open_receipt(request: OpenReceiptRequest):
    """
    Открыть новый чек (fptr.openReceipt)

    Типы чеков:
    - 0: Продажа (LIBFPTR_RT_SELL)
    - 1: Возврат продажи (LIBFPTR_RT_SELL_RETURN)
    - 2: Покупка (LIBFPTR_RT_BUY)
    - 3: Возврат покупки (LIBFPTR_RT_BUY_RETURN)
    - 4: Коррекция продажи (LIBFPTR_RT_SELL_CORRECTION)
    - 5: Коррекция покупки (LIBFPTR_RT_BUY_CORRECTION)
    """
    check_driver()

    try:
        # Устанавливаем тип чека
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, request.receipt_type)

        # Устанавливаем имя кассира
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, request.cashier_name)

        # Если указан email/телефон покупателя
        if request.customer_contact:
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BUYER_EMAIL_OR_PHONE, request.customer_contact)

        # Открываем чек
        result = driver.fptr.openReceipt()

        if result < 0:
            raise AtolDriverError(f"Ошибка открытия чека: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message=f"Чек типа {request.receipt_type} успешно открыт"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/add-item")
async def add_item(request: AddItemRequest):
    """
    Добавить позицию в открытый чек (fptr.registration)

    Регистрация товара/услуги в чеке с указанием всех фискальных реквизитов.
    """
    check_driver()

    try:
        # Устанавливаем параметры товара
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, request.name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, request.price)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, request.quantity)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, request.tax_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE_SIGN, request.payment_method)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_SIGN, request.payment_object)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DEPARTMENT, request.department)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT, request.measure_unit)

        # Регистрируем позицию
        result = driver.fptr.registration()

        if result < 0:
            raise AtolDriverError(f"Ошибка регистрации позиции: {driver.fptr.errorDescription()}")

        total = request.price * request.quantity

        return StatusResponse(
            success=True,
            message=f"Позиция '{request.name}' добавлена (сумма: {total:.2f})"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/add-payment")
async def add_payment(request: AddPaymentRequest):
    """
    Добавить оплату в открытый чек (fptr.payment)

    Типы оплаты:
    - 0: Наличные (LIBFPTR_PT_CASH)
    - 1: Электронные (LIBFPTR_PT_ELECTRONICALLY)
    - 2: Предоплата (LIBFPTR_PT_PREPAID)
    - 3: Постоплата/кредит (LIBFPTR_PT_CREDIT)
    - 4: Прочее (LIBFPTR_PT_OTHER)
    """
    check_driver()

    try:
        # Устанавливаем параметры оплаты
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, request.payment_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, request.amount)

        # Регистрируем оплату
        result = driver.fptr.payment()

        if result < 0:
            raise AtolDriverError(f"Ошибка регистрации оплаты: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message=f"Оплата {request.amount:.2f} добавлена"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/close", response_model=CloseReceiptResponse)
async def close_receipt():
    """
    Закрыть чек и напечатать (fptr.closeReceipt)

    Завершает формирование чека, отправляет данные в ФН и печатает чек.
    Возвращает все фискальные реквизиты напечатанного документа.
    """
    check_driver()

    try:
        # Закрываем чек
        result = driver.fptr.closeReceipt()

        if result < 0:
            raise AtolDriverError(f"Ошибка закрытия чека: {driver.fptr.errorDescription()}")

        # Получаем фискальные данные
        fiscal_data = {
            "success": True,
            "fiscal_document_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
            "fiscal_document_sign": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
            "fiscal_storage_number": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_STORAGE_NUMBER),
            "shift_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            "receipt_number": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            "fiscal_document_datetime": driver.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat() if driver.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME) else None,
            "kkt_number": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),
            "ofd_name": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_OFD_NAME),
            "ofd_inn": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_OFD_INN),
            "ofd_site": driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_OFD_SITE),
            "ffd_version": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FFD_VERSION),
            "fn_life_state": driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_LIFE_STATE),
            "message": "Чек успешно закрыт и напечатан"
        }

        return CloseReceiptResponse(**fiscal_data)

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cancel")
async def cancel_receipt():
    """
    Отменить открытый чек (fptr.cancelReceipt)

    Отменяет формирование текущего чека без печати.
    Используется при ошибках или отмене операции.
    """
    check_driver()

    try:
        result = driver.fptr.cancelReceipt()

        if result < 0:
            raise AtolDriverError(f"Ошибка отмены чека: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Чек успешно отменён"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ДОПОЛНИТЕЛЬНЫЕ ОПЕРАЦИИ ==========

@router.post("/print-text")
async def print_text(text: str, wrap: int = 0, alignment: int = 0):
    """
    Напечатать текстовую строку в чеке (fptr.printText)

    Args:
        text: Текст для печати
        wrap: Перенос строк (0=авто, 1=по словам, 2=по символам)
        alignment: Выравнивание (0=влево, 1=по центру, 2=вправо)
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, text)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT_WRAP, wrap)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, alignment)

        result = driver.fptr.printText()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати текста: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Текст напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/print-barcode")
async def print_barcode(barcode: str, barcode_type: int = 8, scale: int = 2, height: int = 100):
    """
    Напечатать штрих-код в чеке (fptr.printBarcode)

    Args:
        barcode: Данные штрих-кода
        barcode_type: Тип штрих-кода (8=EAN13, 9=EAN8, 10=Code39, и т.д.)
        scale: Масштаб (1-10)
        height: Высота в точках (1-255)
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, barcode)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, barcode_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, scale)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_HEIGHT, height)

        result = driver.fptr.printBarcode()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати штрих-кода: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Штрих-код напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
