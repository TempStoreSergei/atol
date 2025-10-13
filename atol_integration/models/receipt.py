"""
Модели данных для чеков
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import IntEnum


class ReceiptType(IntEnum):
    """Типы чеков"""
    SELL = 0  # Продажа
    SELL_RETURN = 1  # Возврат продажи
    BUY = 2  # Покупка
    BUY_RETURN = 3  # Возврат покупки
    SELL_CORRECTION = 4  # Коррекция продажи
    BUY_CORRECTION = 5  # Коррекция покупки


class PaymentType(IntEnum):
    """Типы оплаты"""
    CASH = 0  # Наличные
    ELECTRONICALLY = 1  # Электронными
    PREPAID = 2  # Предварительная оплата (аванс)
    CREDIT = 3  # Последующая оплата (кредит)
    OTHER = 4  # Иная форма оплаты


class VatType(IntEnum):
    """Типы НДС"""
    NONE = 0  # Без НДС
    VAT0 = 1  # НДС 0%
    VAT10 = 2  # НДС 10%
    VAT20 = 3  # НДС 20%
    VAT110 = 4  # НДС 10/110
    VAT120 = 5  # НДС 20/120


class PaymentMethodType(IntEnum):
    """Признак способа расчета"""
    FULL_PREPAYMENT = 1  # Предоплата 100%
    PARTIAL_PREPAYMENT = 2  # Частичная предоплата
    ADVANCE = 3  # Аванс
    FULL_PAYMENT = 4  # Полный расчет
    PARTIAL_PAYMENT_CREDIT = 5  # Частичный расчет и кредит
    CREDIT = 6  # Передача в кредит
    CREDIT_PAYMENT = 7  # Оплата кредита


class PaymentObjectType(IntEnum):
    """Признак предмета расчета"""
    COMMODITY = 1  # Товар
    EXCISE = 2  # Подакцизный товар
    JOB = 3  # Работа
    SERVICE = 4  # Услуга
    GAMBLING_BET = 5  # Ставка азартной игры
    GAMBLING_PRIZE = 6  # Выигрыш азартной игры
    LOTTERY = 7  # Лотерейный билет
    LOTTERY_PRIZE = 8  # Выигрыш лотереи
    INTELLECTUAL = 9  # Предоставление РИД
    PAYMENT = 10  # Платеж
    AGENT_COMMISSION = 11  # Агентское вознаграждение
    COMPOSITE = 12  # Составной предмет расчета
    OTHER = 13  # Иной предмет расчета


@dataclass
class Item:
    """Позиция чека"""
    name: str
    price: float
    quantity: float = 1.0
    amount: float = 0.0
    vat: VatType = VatType.NONE
    payment_method: PaymentMethodType = PaymentMethodType.FULL_PAYMENT
    payment_object: PaymentObjectType = PaymentObjectType.COMMODITY
    measure_unit: str = "шт"
    department: int = 1

    def __post_init__(self):
        if self.amount == 0.0:
            self.amount = round(self.price * self.quantity, 2)


@dataclass
class Payment:
    """Оплата"""
    type: PaymentType
    sum: float


@dataclass
class Receipt:
    """Чек"""
    type: ReceiptType
    items: List[Item] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    email: Optional[str] = None
    phone: Optional[str] = None

    def add_item(self, item: Item):
        """Добавить позицию"""
        self.items.append(item)

    def add_payment(self, payment: Payment):
        """Добавить оплату"""
        self.payments.append(payment)

    @property
    def total(self) -> float:
        """Общая сумма чека"""
        return sum(item.amount for item in self.items)
