"""
Pydantic схемы для FastAPI
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ========== REQUEST SCHEMAS ==========

class ConnectRequest(BaseModel):
    """Запрос на подключение к ККТ"""
    connection_type: str = Field("tcp", description="Тип подключения: tcp, usb, serial, bluetooth")
    host: Optional[str] = Field("localhost", description="IP адрес для TCP")
    port: Optional[int] = Field(5555, description="Порт для TCP")
    serial_port: Optional[str] = Field(None, description="COM порт для Serial")
    baudrate: Optional[int] = Field(115200, description="Скорость для Serial")


class OpenShiftRequest(BaseModel):
    """Запрос на открытие смены"""
    cashier_name: str = Field("Кассир", description="Имя кассира")


class CloseShiftRequest(BaseModel):
    """Запрос на закрытие смены"""
    cashier_name: str = Field("Кассир", description="Имя кассира")


class OpenReceiptRequest(BaseModel):
    """Запрос на открытие чека"""
    receipt_type: int = Field(0, description="Тип чека: 0-продажа, 1-возврат, 2-покупка, 3-возврат покупки")
    cashier_name: str = Field("Кассир", description="Имя кассира")
    email: Optional[str] = Field(None, description="Email покупателя")
    phone: Optional[str] = Field(None, description="Телефон покупателя")


class AddItemRequest(BaseModel):
    """Запрос на добавление товара"""
    name: str = Field(..., description="Название товара")
    price: float = Field(..., description="Цена за единицу", gt=0)
    quantity: float = Field(1.0, description="Количество", gt=0)
    tax_type: int = Field(0, description="Тип НДС: 0-без НДС, 1-0%, 2-10%, 3-20%, 4-10/110, 5-20/120")
    department: int = Field(1, description="Номер отдела")
    measure_unit: str = Field("шт", description="Единица измерения")


class AddPaymentRequest(BaseModel):
    """Запрос на добавление оплаты"""
    amount: float = Field(..., description="Сумма оплаты", gt=0)
    payment_type: int = Field(0, description="Тип оплаты: 0-наличные, 1-электронные, 2-предоплата, 3-кредит, 4-другое")


class CashOperationRequest(BaseModel):
    """Запрос на денежную операцию"""
    amount: float = Field(..., description="Сумма", gt=0)


class OpenCorrectionReceiptRequest(BaseModel):
    """Запрос на открытие чека коррекции"""
    correction_type: int = Field(0, description="Тип коррекции: 0-самостоятельно, 1-по предписанию")
    base_date: Optional[str] = Field(None, description="Дата документа основания (DD.MM.YYYY)")
    base_number: Optional[str] = Field(None, description="Номер документа основания")
    base_name: Optional[str] = Field(None, description="Наименование документа основания")
    cashier_name: str = Field("Кассир", description="Имя кассира")


class AddCorrectionItemRequest(BaseModel):
    """Запрос на добавление позиции коррекции"""
    amount: float = Field(..., description="Сумма коррекции", gt=0)
    tax_type: int = Field(0, description="Тип НДС")
    description: str = Field("Коррекция", description="Описание")


class CreateReceiptRequest(BaseModel):
    """Полный запрос на создание чека (все в одном)"""
    receipt_type: int = Field(0, description="Тип чека")
    cashier_name: str = Field("Кассир", description="Имя кассира")
    email: Optional[str] = Field(None, description="Email покупателя")
    phone: Optional[str] = Field(None, description="Телефон покупателя")
    items: List[AddItemRequest] = Field(..., description="Список товаров")
    payments: List[AddPaymentRequest] = Field(..., description="Список оплат")


# ========== RESPONSE SCHEMAS ==========

class StatusResponse(BaseModel):
    """Базовый ответ о статусе"""
    success: bool
    message: Optional[str] = None


class DeviceInfoResponse(BaseModel):
    """Информация об устройстве"""
    model: str
    serial_number: str
    firmware_version: str
    fiscal_mode: bool
    fn_serial: str
    fn_fiscal_sign: str
    inn: str
    reg_number: str


class ShiftStatusResponse(BaseModel):
    """Статус смены"""
    opened: bool
    number: int
    receipt_count: int


class ReceiptResponse(BaseModel):
    """Результат закрытия чека"""
    success: bool
    fiscal_document_number: int
    fiscal_sign: int
    shift_number: int
    receipt_number: int
    datetime: str


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str
    detail: Optional[str] = None
