"""
Базовый пример использования
"""
from atol_integration.api.client import AtolClient
from atol_integration.models.receipt import Receipt, Item, Payment, ReceiptType, PaymentType, VatType
from atol_integration.config.settings import settings


def main():
    # Создание клиента
    client = AtolClient(
        base_url=settings.atol_api_url,
        login=settings.atol_login,
        password=settings.atol_password
    )

    # Создание чека
    receipt = Receipt(type=ReceiptType.SELL)

    # Добавление товаров
    receipt.add_item(Item(
        name="Товар 1",
        price=100.50,
        quantity=2,
        vat=VatType.VAT20
    ))

    receipt.add_item(Item(
        name="Товар 2",
        price=250.00,
        quantity=1,
        vat=VatType.VAT20
    ))

    # Добавление оплаты
    receipt.add_payment(Payment(
        type=PaymentType.CASH,
        sum=receipt.total
    ))

    print(f"Общая сумма чека: {receipt.total}")

    # Отправка чека (TODO: реализовать)
    # result = client.create_receipt(receipt)


if __name__ == "__main__":
    main()
