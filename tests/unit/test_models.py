"""
Тесты моделей данных
"""
import pytest
from atol_integration.models.receipt import Item, Receipt, Payment, ReceiptType, PaymentType, VatType


def test_item_creation():
    """Тест создания позиции"""
    item = Item(name="Тестовый товар", price=100.0, quantity=2)
    assert item.amount == 200.0


def test_receipt_total():
    """Тест расчета суммы чека"""
    receipt = Receipt(type=ReceiptType.SELL)
    receipt.add_item(Item(name="Товар 1", price=100, quantity=1))
    receipt.add_item(Item(name="Товар 2", price=200, quantity=2))

    assert receipt.total == 500.0
