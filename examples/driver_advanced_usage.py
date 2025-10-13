"""
Расширенные примеры работы с драйвером АТОЛ
"""
from atol_integration.api.driver import (
    AtolDriver,
    ConnectionType,
    ReceiptType,
    PaymentType,
    TaxType
)
from datetime import datetime


def example_return_receipt():
    """Пример чека возврата"""
    print("=" * 60)
    print("Пример: Чек возврата")
    print("=" * 60)

    driver = AtolDriver()

    try:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        # Открываем чек возврата
        driver.open_receipt(
            receipt_type=ReceiptType.SELL_RETURN,
            cashier_name="Иванов И.И.",
            email="customer@example.com"
        )

        # Добавляем возвращаемый товар
        driver.add_item(
            name="Молоко 3.2%",
            price=85.50,
            quantity=1.0,
            tax_type=TaxType.VAT10
        )

        # Возврат наличными
        driver.add_payment(85.50, PaymentType.CASH)

        result = driver.close_receipt()
        print(f"Возврат выполнен. ФД: {result['fiscal_document_number']}")

    finally:
        driver.disconnect()


def example_mixed_payment():
    """Пример смешанной оплаты (наличные + карта)"""
    print("\n" + "=" * 60)
    print("Пример: Смешанная оплата")
    print("=" * 60)

    driver = AtolDriver()

    try:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        driver.open_receipt(
            receipt_type=ReceiptType.SELL,
            cashier_name="Петров П.П."
        )

        # Добавляем товары на большую сумму
        driver.add_item(
            name="Ноутбук Lenovo",
            price=45000.00,
            quantity=1.0,
            tax_type=TaxType.VAT20,
            measure_unit="шт"
        )

        driver.add_item(
            name="Мышь беспроводная",
            price=1500.00,
            quantity=1.0,
            tax_type=TaxType.VAT20,
            measure_unit="шт"
        )

        total = 46500.00

        # Оплата частично наличными, частично картой
        driver.add_payment(10000.00, PaymentType.CASH)  # 10000 наличными
        driver.add_payment(36500.00, PaymentType.ELECTRONICALLY)  # 36500 картой

        result = driver.close_receipt()
        print(f"Чек пробит со смешанной оплатой. ФД: {result['fiscal_document_number']}")

    finally:
        driver.disconnect()


def example_correction_receipt():
    """Пример чека коррекции"""
    print("\n" + "=" * 60)
    print("Пример: Чек коррекции")
    print("=" * 60)

    driver = AtolDriver()

    try:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        # Открываем чек коррекции (самостоятельная)
        driver.open_correction_receipt(
            correction_type=0,  # Самостоятельная коррекция
            base_date=datetime.now().strftime("%d.%m.%Y"),
            base_number="КР-001",
            base_name="Акт о возврате денежных средств покупателю",
            cashier_name="Иванов И.И."
        )

        # Добавляем сумму коррекции
        driver.add_correction_item(
            amount=1000.00,
            tax_type=TaxType.VAT20,
            description="Коррекция продажи от 01.01.2024"
        )

        # Добавляем оплату
        driver.add_payment(1000.00, PaymentType.CASH)

        result = driver.close_receipt()
        print(f"Чек коррекции пробит. ФД: {result['fiscal_document_number']}")

    finally:
        driver.disconnect()


def example_cash_operations():
    """Пример денежных операций (внесение/выплата)"""
    print("\n" + "=" * 60)
    print("Пример: Внесение и выплата денег")
    print("=" * 60)

    driver = AtolDriver()

    try:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        # Внесение денег в кассу
        print("Внесение 5000 руб в кассу...")
        driver.cash_income(5000.00)
        print("Успешно")

        # Выплата денег из кассы
        print("Выплата 2000 руб из кассы...")
        driver.cash_outcome(2000.00)
        print("Успешно")

    finally:
        driver.disconnect()


def example_shift_operations():
    """Пример управления сменой"""
    print("\n" + "=" * 60)
    print("Пример: Управление сменой")
    print("=" * 60)

    driver = AtolDriver()

    try:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        # Проверяем статус смены
        status = driver.get_shift_status()
        print(f"Статус смены: {'Открыта' if status['opened'] else 'Закрыта'}")
        print(f"Номер смены: {status['number']}")
        print(f"Количество чеков: {status['receipt_count']}")

        # Если смена закрыта - открываем
        if not status['opened']:
            print("\nОткрываем смену...")
            driver.open_shift(cashier_name="Иванов И.И.")
            print("Смена открыта")

        # Печатаем X-отчет (без гашения)
        print("\nПечать X-отчета...")
        driver.x_report()
        print("X-отчет распечатан")

        # Закрываем смену
        print("\nЗакрываем смену...")
        driver.close_shift(cashier_name="Иванов И.И.")
        print("Смена закрыта (Z-отчет)")

    finally:
        driver.disconnect()


def example_context_manager():
    """Пример использования контекстного менеджера"""
    print("\n" + "=" * 60)
    print("Пример: Использование контекстного менеджера")
    print("=" * 60)

    # Драйвер автоматически подключится и отключится
    with AtolDriver() as driver:
        driver.connect(ConnectionType.TCP, "192.168.1.100", 5555)

        info = driver.get_device_info()
        print(f"Модель: {info['model']}")
        print(f"Серийный номер: {info['serial_number']}")

        # Открываем денежный ящик
        driver.open_cash_drawer()
        print("Денежный ящик открыт")

    # Драйвер автоматически отключится при выходе из контекста
    print("Автоматическое отключение")


def example_usb_connection():
    """Пример подключения по USB"""
    print("\n" + "=" * 60)
    print("Пример: Подключение по USB")
    print("=" * 60)

    driver = AtolDriver()

    try:
        # Подключение по USB (автоматический поиск устройства)
        driver.connect(connection_type=ConnectionType.USB)

        info = driver.get_device_info()
        print(f"Подключено по USB: {info['model']}")

    finally:
        driver.disconnect()


def example_serial_connection():
    """Пример подключения по Serial (COM-порт)"""
    print("\n" + "=" * 60)
    print("Пример: Подключение по COM-порту")
    print("=" * 60)

    driver = AtolDriver()

    try:
        # Подключение по COM-порту
        driver.connect(
            connection_type=ConnectionType.SERIAL,
            serial_port="COM3",
            baudrate=115200
        )

        info = driver.get_device_info()
        print(f"Подключено по COM3: {info['model']}")

    finally:
        driver.disconnect()


if __name__ == "__main__":
    print("Расширенные примеры работы с драйвером АТОЛ\n")

    try:
        # Запускаем все примеры
        example_return_receipt()
        example_mixed_payment()
        example_correction_receipt()
        example_cash_operations()
        example_shift_operations()
        example_context_manager()
        # example_usb_connection()  # Раскомментируйте если есть USB подключение
        # example_serial_connection()  # Раскомментируйте если есть COM подключение

    except Exception as e:
        print(f"\nОшибка при выполнении примеров: {e}")
        print("Убедитесь что ККТ подключена и настроена правильно")
