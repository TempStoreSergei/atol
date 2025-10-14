"""
Драйвер для работы с АТОЛ ККТ через libfptr10
"""
from typing import Optional, Dict, Any, List
import logging
from enum import IntEnum
from .libfptr10 import IFptr


logger = logging.getLogger(__name__)


class ConnectionType(IntEnum):
    """Типы подключения к ККТ"""
    USB = 0
    SERIAL = 1
    TCP = 2
    BLUETOOTH = 3


class ReceiptType(IntEnum):
    """Типы чеков"""
    SELL = 0  # Продажа
    SELL_RETURN = 1  # Возврат продажи
    BUY = 2  # Покупка
    BUY_RETURN = 3  # Возврат покупки
    SELL_CORRECTION = 4  # Коррекция продажи
    BUY_CORRECTION = 5  # Коррекция покупки


class TaxType(IntEnum):
    """Типы налогов (НДС)"""
    NONE = 0  # Без НДС
    VAT0 = 1  # НДС 0%
    VAT10 = 2  # НДС 10%
    VAT20 = 3  # НДС 20%
    VAT110 = 4  # НДС 10/110
    VAT120 = 5  # НДС 20/120


class PaymentType(IntEnum):
    """Типы оплаты"""
    CASH = 0  # Наличные
    ELECTRONICALLY = 1  # Электронными
    PREPAID = 2  # Предварительная оплата (аванс)
    CREDIT = 3  # Последующая оплата (кредит)
    OTHER = 4  # Иная форма оплаты


class AtolDriverError(Exception):
    """Базовое исключение для ошибок драйвера АТОЛ"""
    pass


class AtolDriver:
    """Драйвер для работы с АТОЛ ККТ через libfptr10"""

    def __init__(self):
        """Инициализация драйвера"""
        self.fptr = None
        self._connected = False

        try:
            self.fptr = IFptr()
            logger.info("АТОЛ драйвер инициализирован")
        except ImportError:
            logger.error("Библиотека libfptr10 не найдена. Установите драйвер АТОЛ ККТ v.10")
            raise AtolDriverError("libfptr10 не установлена")

    def set_param(self, param: int, value: Any) -> None:
        """Установить параметр драйвера"""
        if not self.fptr:
            raise AtolDriverError("Драйвер не инициализирован")
        self.fptr.setParam(param, value)

    def get_param(self, param: int) -> Any:
        """Получить параметр драйвера"""
        if not self.fptr:
            raise AtolDriverError("Драйвер не инициализирован")
        return self.fptr.getParamInt(param)

    def get_param_string(self, param: int) -> str:
        """Получить строковый параметр драйвера"""
        if not self.fptr:
            raise AtolDriverError("Драйвер не инициализирован")
        return self.fptr.getParamString(param)

    def connect(
        self,
        connection_type: ConnectionType = ConnectionType.TCP,
        host: str = "localhost",
        port: int = 5555,
        serial_port: Optional[str] = None,
        baudrate: int = 115200
    ) -> bool:
        """
        Подключиться к ККТ

        Args:
            connection_type: Тип подключения
            host: IP адрес для TCP подключения
            port: Порт для TCP подключения
            serial_port: COM порт для Serial подключения
            baudrate: Скорость для Serial подключения
        """
        try:
            # Константы из libfptr10
            LIBFPTR_PARAM_DATA_TYPE = 1001
            LIBFPTR_PARAM_PORT = 1002
            LIBFPTR_PARAM_IPADDRESS = 1003
            LIBFPTR_PARAM_IPPORT = 1004
            LIBFPTR_PARAM_BAUDRATE = 1005

            if connection_type == ConnectionType.TCP:
                self.set_param(LIBFPTR_PARAM_DATA_TYPE, ConnectionType.TCP)
                self.set_param(LIBFPTR_PARAM_IPADDRESS, host)
                self.set_param(LIBFPTR_PARAM_IPPORT, port)
                logger.info(f"Подключение к ККТ по TCP: {host}:{port}")
            elif connection_type == ConnectionType.SERIAL:
                if not serial_port:
                    raise AtolDriverError("Не указан COM порт")
                self.set_param(LIBFPTR_PARAM_DATA_TYPE, ConnectionType.SERIAL)
                self.set_param(LIBFPTR_PARAM_PORT, serial_port)
                self.set_param(LIBFPTR_PARAM_BAUDRATE, baudrate)
                logger.info(f"Подключение к ККТ по Serial: {serial_port}")
            elif connection_type == ConnectionType.USB:
                self.set_param(LIBFPTR_PARAM_DATA_TYPE, ConnectionType.USB)
                logger.info("Подключение к ККТ по USB")

            result = self.fptr.open()
            if result < 0:
                error = self.get_param_string(1)
                raise AtolDriverError(f"Ошибка подключения: {error}")

            self._connected = True
            logger.info("Успешное подключение к ККТ")
            return True

        except Exception as e:
            logger.error(f"Ошибка подключения к ККТ: {e}")
            raise AtolDriverError(f"Не удалось подключиться: {e}")

    def disconnect(self) -> None:
        """Отключиться от ККТ"""
        if self.fptr and self._connected:
            self.fptr.close()
            self._connected = False
            logger.info("Отключение от ККТ")

    def is_connected(self) -> bool:
        """Проверить подключение"""
        return self._connected

    def _check_result(self, result: int, operation: str = "") -> None:
        """Проверить результат операции"""
        if result < 0:
            error = self.get_param_string(1)
            raise AtolDriverError(f"Ошибка {operation}: {error}")

    # ========== ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ ==========

    def get_device_info(self) -> Dict[str, Any]:
        """Получить информацию об устройстве"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.queryData()
            self._check_result(result, "получения информации об устройстве")

            return {
                "model": self.get_param_string(108),  # Model
                "serial_number": self.get_param_string(101),  # Serial number
                "firmware_version": self.get_param_string(102),  # Firmware version
                "fiscal_mode": self.get_param(103) == 1,  # Is fiscal
                "fn_serial": self.get_param_string(104),  # FN serial number
                "fn_fiscal_sign": self.get_param_string(105),  # FN fiscal sign
                "inn": self.get_param_string(106),  # INN
                "reg_number": self.get_param_string(107),  # Registration number
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            raise

    def get_shift_status(self) -> Dict[str, Any]:
        """Получить статус смены"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.getShiftStatus()
            self._check_result(result, "получения статуса смены")

            return {
                "opened": self.get_param(1) == 1,  # Shift opened
                "number": self.get_param(2),  # Shift number
                "receipt_count": self.get_param(3),  # Receipt count
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса смены: {e}")
            raise

    # ========== УПРАВЛЕНИЕ СМЕНОЙ ==========

    def open_shift(self, cashier_name: str = "Кассир") -> Dict[str, Any]:
        """
        Открыть смену

        Args:
            cashier_name: Имя кассира
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Проверяем статус смены
            shift_status = self.get_shift_status()
            if shift_status["opened"]:
                logger.warning("Смена уже открыта")
                return shift_status

            # Устанавливаем кассира
            self.set_param(1021, cashier_name)  # Operator name

            # Открываем смену
            result = self.fptr.openShift()
            self._check_result(result, "открытия смены")

            logger.info("Смена открыта")
            return self.get_shift_status()

        except Exception as e:
            logger.error(f"Ошибка открытия смены: {e}")
            raise

    def close_shift(self, cashier_name: str = "Кассир") -> Dict[str, Any]:
        """
        Закрыть смену

        Args:
            cashier_name: Имя кассира
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Устанавливаем кассира
            self.set_param(1021, cashier_name)

            # Закрываем смену
            result = self.fptr.closeShift()
            self._check_result(result, "закрытия смены")

            logger.info("Смена закрыта")
            return {"success": True}

        except Exception as e:
            logger.error(f"Ошибка закрытия смены: {e}")
            raise

    # ========== ОПЕРАЦИИ С ЧЕКАМИ ==========

    def open_receipt(
        self,
        receipt_type: ReceiptType = ReceiptType.SELL,
        cashier_name: str = "Кассир",
        email: Optional[str] = None,
        phone: Optional[str] = None
    ) -> bool:
        """
        Открыть чек

        Args:
            receipt_type: Тип чека
            cashier_name: Имя кассира
            email: Email покупателя
            phone: Телефон покупателя
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Устанавливаем тип чека
            self.set_param(1001, receipt_type)

            # Устанавливаем кассира
            self.set_param(1021, cashier_name)

            # Устанавливаем контакт покупателя
            if email:
                self.set_param(1008, email)
            if phone:
                self.set_param(1008, phone)

            # Открываем чек
            result = self.fptr.openReceipt()
            self._check_result(result, "открытия чека")

            logger.info(f"Чек открыт: тип {receipt_type}")
            return True

        except Exception as e:
            logger.error(f"Ошибка открытия чека: {e}")
            raise

    def add_item(
        self,
        name: str,
        price: float,
        quantity: float = 1.0,
        tax_type: TaxType = TaxType.NONE,
        department: int = 1,
        measure_unit: str = "шт"
    ) -> bool:
        """
        Добавить товар в чек

        Args:
            name: Название товара
            price: Цена за единицу
            quantity: Количество
            tax_type: Тип НДС
            department: Номер отдела/секции
            measure_unit: Единица измерения
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Устанавливаем параметры товара
            self.set_param(1030, name)  # Name
            self.set_param(1000, price)  # Price
            self.set_param(1023, quantity)  # Quantity
            self.set_param(1199, tax_type)  # Tax type
            self.set_param(1068, department)  # Department
            self.set_param(1197, measure_unit)  # Measure unit

            # Регистрируем товар
            result = self.fptr.registration()
            self._check_result(result, "регистрации товара")

            logger.debug(f"Товар добавлен: {name}, цена {price}, кол-во {quantity}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления товара: {e}")
            raise

    def add_payment(
        self,
        amount: float,
        payment_type: PaymentType = PaymentType.CASH
    ) -> bool:
        """
        Добавить оплату

        Args:
            amount: Сумма оплаты
            payment_type: Тип оплаты
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Устанавливаем параметры оплаты
            self.set_param(1031, amount)  # Sum
            self.set_param(1001, payment_type)  # Payment type

            # Регистрируем оплату
            result = self.fptr.payment()
            self._check_result(result, "регистрации оплаты")

            logger.debug(f"Оплата добавлена: {amount}, тип {payment_type}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления оплаты: {e}")
            raise

    def close_receipt(self) -> Dict[str, Any]:
        """Закрыть чек и напечатать"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Закрываем чек
            result = self.fptr.closeReceipt()
            self._check_result(result, "закрытия чека")

            # Получаем данные о чеке
            receipt_data = {
                "success": True,
                "fiscal_document_number": self.get_param(1054),  # FD number
                "fiscal_sign": self.get_param(1077),  # FP
                "shift_number": self.get_param(1038),  # Shift number
                "receipt_number": self.get_param(1042),  # Receipt number
                "datetime": self.get_param_string(1012),  # Datetime
            }

            logger.info("Чек закрыт успешно")
            return receipt_data

        except Exception as e:
            logger.error(f"Ошибка закрытия чека: {e}")
            raise

    def cancel_receipt(self) -> bool:
        """Отменить текущий чек"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.cancelReceipt()
            self._check_result(result, "отмены чека")
            logger.info("Чек отменен")
            return True
        except Exception as e:
            logger.error(f"Ошибка отмены чека: {e}")
            raise

    # ========== ДЕНЕЖНЫЕ ОПЕРАЦИИ ==========

    def cash_income(self, amount: float) -> bool:
        """
        Внесение наличных

        Args:
            amount: Сумма для внесения
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            self.set_param(1031, amount)
            result = self.fptr.cashIncome()
            self._check_result(result, "внесения наличных")
            logger.info(f"Внесено наличных: {amount}")
            return True
        except Exception as e:
            logger.error(f"Ошибка внесения наличных: {e}")
            raise

    def cash_outcome(self, amount: float) -> bool:
        """
        Выплата наличных

        Args:
            amount: Сумма для выплаты
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            self.set_param(1031, amount)
            result = self.fptr.cashOutcome()
            self._check_result(result, "выплаты наличных")
            logger.info(f"Выплачено наличных: {amount}")
            return True
        except Exception as e:
            logger.error(f"Ошибка выплаты наличных: {e}")
            raise

    # ========== ОТЧЕТЫ ==========

    def x_report(self) -> bool:
        """Печать X-отчета (без гашения)"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.report()
            self._check_result(result, "печати X-отчета")
            logger.info("X-отчет распечатан")
            return True
        except Exception as e:
            logger.error(f"Ошибка печати X-отчета: {e}")
            raise

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def beep(self) -> bool:
        """Издать звуковой сигнал"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # self.set_param(LIBFPTR_PARAM_FREQUENCY, host)
            self.set_param(IFptr.LIBFPTR_PARAM_DURATION, 10)
            result = self.fptr.beep()
            self._check_result(result, "подачи сигнала")
            return True
        except Exception as e:
            logger.error(f"Ошибка подачи сигнала: {e}")
            raise

    def play_portal_melody(self) -> bool:
        """
        Сыграть мелодию "Want You Gone" из Portal 2 через динамик ККТ!

        🎵 Well here we are again, it's always such a pleasure... 🎵
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        import time

        logger.info("🎵 Начинаем проигрывать Portal 2 - Want You Gone!")

        # Нотная запись упрощенной версии мелодии
        # (нота, длительность в секундах)
        # Используем базовый beep, т.к. не все драйверы поддерживают частоты
        melody = [
            # "Well here we are again"
            (0.1, 0.15), (0.1, 0.15), (0.1, 0.3),
            # "It's always such a pleasure"
            (0.1, 0.15), (0.1, 0.15), (0.1, 0.15), (0.1, 0.3),
            # Пауза
            (0, 0.2),
            # "Remember when you tried to kill me twice?"
            (0.1, 0.15), (0.1, 0.15), (0.1, 0.15), (0.1, 0.15),
            (0.1, 0.15), (0.1, 0.3),
            # Пауза
            (0, 0.3),
            # Финальная фраза
            (0.1, 0.2), (0.1, 0.2), (0.1, 0.4),
            # Завершающий аккорд
            (0.1, 0.6),
        ]

        try:
            for duration, pause in melody:
                if duration > 0:
                    # Издаем звук
                    self.fptr.beep()
                # Пауза между нотами
                time.sleep(pause)

            logger.info("🎵 Мелодия завершена! Спасибо за использование Aperture Science!")
            return True

        except Exception as e:
            logger.error(f"Ошибка проигрывания мелодии: {e}")
            raise AtolDriverError(f"Не удалось сыграть мелодию: {e}")

    def open_cash_drawer(self) -> bool:
        """Открыть денежный ящик"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.openCashDrawer()
            self._check_result(result, "открытия денежного ящика")
            logger.info("Денежный ящик открыт")
            return True
        except Exception as e:
            logger.error(f"Ошибка открытия денежного ящика: {e}")
            raise

    def cut_paper(self) -> bool:
        """Отрезать чек"""
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            result = self.fptr.cut()
            self._check_result(result, "отрезания чека")
            return True
        except Exception as e:
            logger.error(f"Ошибка отрезания чека: {e}")
            raise

    # ========== ЧЕКИ КОРРЕКЦИИ ==========

    def open_correction_receipt(
        self,
        correction_type: int = 0,  # 0 - самостоятельно, 1 - по предписанию
        base_date: Optional[str] = None,
        base_number: Optional[str] = None,
        base_name: Optional[str] = None,
        cashier_name: str = "Кассир"
    ) -> bool:
        """
        Открыть чек коррекции

        Args:
            correction_type: Тип коррекции (0 - самостоятельная, 1 - по предписанию)
            base_date: Дата документа основания (формат DD.MM.YYYY)
            base_number: Номер документа основания
            base_name: Наименование документа основания
            cashier_name: Имя кассира
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            # Устанавливаем тип коррекции
            self.set_param(1173, correction_type)  # Correction type

            # Устанавливаем документ основания
            if base_date:
                self.set_param(1178, base_date)  # Correction base date
            if base_number:
                self.set_param(1179, base_number)  # Correction base number
            if base_name:
                self.set_param(1177, base_name)  # Correction base name

            # Устанавливаем кассира
            self.set_param(1021, cashier_name)

            # Открываем чек коррекции
            result = self.fptr.openCorrection()
            self._check_result(result, "открытия чека коррекции")

            logger.info("Чек коррекции открыт")
            return True

        except Exception as e:
            logger.error(f"Ошибка открытия чека коррекции: {e}")
            raise

    def add_correction_item(
        self,
        amount: float,
        tax_type: TaxType = TaxType.NONE,
        description: str = "Коррекция"
    ) -> bool:
        """
        Добавить сумму в чек коррекции

        Args:
            amount: Сумма коррекции
            tax_type: Тип НДС
            description: Описание
        """
        if not self._connected:
            raise AtolDriverError("Нет подключения к ККТ")

        try:
            self.set_param(1031, amount)  # Sum
            self.set_param(1199, tax_type)  # Tax type
            self.set_param(1177, description)  # Description

            result = self.fptr.correctionRegistration()
            self._check_result(result, "регистрации коррекции")

            logger.debug(f"Коррекция добавлена: {amount}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления коррекции: {e}")
            raise

    def __enter__(self):
        """Контекстный менеджер: вход"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        self.disconnect()
