"""
Базовый пример работы с драйвером АТОЛ
"""
from atol_integration.api.driver import (
    AtolDriver,
    ConnectionType,
    ReceiptType,
    PaymentType,
    TaxType
)


def main():
    """Пример продажи товаров через драйвер"""

    # Создаем экземпляр драйвера
    driver = AtolDriver()

    try:
        # Подключаемся к ККТ по TCP
        print("Подключение к ККТ...")
        driver.connect(
            connection_type=ConnectionType.TCP,
            host="192.168.1.100",  # IP адрес ККТ
            port=5555
        )

        # Получаем информацию об устройстве
        info = driver.get_device_info()
        print(f"\nИнформация об устройстве:")
        print(f"  Модель: {info['model']}")
        print(f"  Серийный номер: {info['serial_number']}")
        print(f"  Версия ПО: {info['firmware_version']}")
        print(f"  ИНН: {info['inn']}")
        print(f"  РН ККТ: {info['reg_number']}")

        # Проверяем статус смены
        shift_status = driver.get_shift_status()
        print(f"\nСтатус смены:")
        print(f"  Открыта: {shift_status['opened']}")
        print(f"  Номер смены: {shift_status['number']}")

        # Открываем смену если закрыта
        if not shift_status['opened']:
            print("\nОткрываем смену...")
            driver.open_shift(cashier_name="Иванов И.И.")

        # Открываем чек продажи
        print("\nОткрываем чек...")
        driver.open_receipt(
            receipt_type=ReceiptType.SELL,
            cashier_name="Иванов И.И.",
            email="customer@example.com"
        )

        # Добавляем товары
        print("Добавляем товары...")
        driver.add_item(
            name="Молоко 3.2%",
            price=85.50,
            quantity=2.0,
            tax_type=TaxType.VAT10,
            measure_unit="шт"
        )

        driver.add_item(
            name="Хлеб белый",
            price=45.00,
            quantity=1.0,
            tax_type=TaxType.VAT10,
            measure_unit="шт"
        )

        # Добавляем оплату наличными
        print("Добавляем оплату...")
        total = 85.50 * 2 + 45.00
        driver.add_payment(
            amount=total,
            payment_type=PaymentType.CASH
        )

        # Закрываем чек
        print("Закрываем чек...")
        receipt_result = driver.close_receipt()
        print(f"\nЧек успешно пробит!")
        print(f"  Номер ФД: {receipt_result['fiscal_document_number']}")
        print(f"  ФП: {receipt_result['fiscal_sign']}")
        print(f"  Номер чека: {receipt_result['receipt_number']}")
        print(f"  Дата и время: {receipt_result['datetime']}")

        # Подаем звуковой сигнал
        driver.beep()

    except Exception as e:
        print(f"Ошибка: {e}")
        # Отменяем чек в случае ошибки
        try:
            driver.cancel_receipt()
        except:
            pass

    finally:
        # Отключаемся от ККТ
        driver.disconnect()
        print("\nОтключение от ККТ")


if __name__ == "__main__":
    main()
