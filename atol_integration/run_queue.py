import json
import datetime
from typing import Any, Dict
import redis
from atol_integration.api.driver import AtolDriver, AtolDriverError
from atol_integration.api.libfptr10 import IFptr
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger


class CommandProcessor:
    """Процессор команд для ККТ с использованием паттерна инкапсуляции"""

    def __init__(self):
        """Инициализация процессора с драйвером ККТ"""
        self.driver = AtolDriver()
        self.fptr = self.driver.fptr

    def _check_result(self, result: int, operation: str):
        """Проверяет результат выполнения операции драйвера"""
        if result < 0:
            error_description = self.fptr.errorDescription()
            error_code = self.fptr.errorCode()
            raise AtolDriverError(f"Ошибка {operation}: {error_description}", error_code=error_code)

    def _play_beep(self, frequency: int = 2000, duration: int = 100):
        """
        Воспроизвести звуковой сигнал

        Args:
            frequency: Частота в Гц
            duration: Длительность в мс
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FREQUENCY, frequency)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DURATION, duration)
        self._check_result(self.fptr.beep(), "подачи звукового сигнала")

    def _play_arcane_melody(self):
        """
        Сыграть мелодию "Enemy" из Arcane (Imagine Dragons feat. JID)

        🎵 I wake up to the sounds of the silence that allows... 🎵
        """
        logger.info("🎵 Начинаем проигрывать 'Enemy' из Arcane!")

        # Упрощённая мелодия "Enemy" - главная тема
        # Формат: (частота в Гц, длительность в мс)
        melody = [
            # "Look out for yourself"
            (392, 200),  # G4
            (392, 200),  # G4
            (440, 300),  # A4
            (392, 200),  # G4
            (100, 150),  # Пауза

            # "I wake up to the sounds"
            (349, 200),  # F4
            (392, 200),  # G4
            (440, 200),  # A4
            (494, 400),  # B4
            (100, 150),  # Пауза

            # "Of the silence that allows"
            (523, 250),  # C5
            (494, 250),  # B4
            (440, 250),  # A4
            (392, 400),  # G4
            (100, 200),  # Пауза

            # "For my mind to run around"
            (440, 200),  # A4
            (392, 200),  # G4
            (349, 200),  # F4
            (392, 200),  # G4
            (440, 400),  # A4
            (100, 150),  # Пауза

            # "With my ear up to the ground"
            (523, 300),  # C5
            (494, 200),  # B4
            (440, 200),  # A4
            (392, 500),  # G4
            (100, 200),  # Пауза

            # Припев: "Everybody wants to be my enemy"
            (392, 150),  # G4
            (392, 150),  # G4
            (440, 150),  # A4
            (440, 150),  # A4
            (494, 300),  # B4
            (523, 300),  # C5
            (100, 100),  # Пауза

            (523, 200),  # C5
            (494, 200),  # B4
            (440, 200),  # A4
            (392, 400),  # G4
            (100, 150),  # Пауза

            # "Spare the sympathy"
            (349, 200),  # F4
            (392, 200),  # G4
            (440, 300),  # A4
            (494, 500),  # B4
            (100, 200),  # Пауза

            # "Everybody wants to be"
            (523, 200),  # C5
            (523, 200),  # C5
            (494, 200),  # B4
            (440, 200),  # A4
            (392, 400),  # G4
            (100, 150),  # Пауза

            # "My enemy-y-y-y-y"
            (587, 250),  # D5
            (523, 250),  # C5
            (494, 250),  # B4
            (440, 250),  # A4
            (392, 600),  # G4
            (100, 200),  # Пауза

            # Финальный аккорд
            (392, 800),  # G4
        ]

        try:
            for frequency, duration in melody:
                self._play_beep(frequency, duration)

            logger.info("🎵 Мелодия 'Enemy' завершена! ⚔️")
            return True

        except Exception as e:
            logger.error(f"Ошибка проигрывания мелодии: {e}")
            raise AtolDriverError(f"Не удалось сыграть мелодию: {e}")

    def process_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение команды на основе полученной из pubsub"""
        response = {
            "command_id": command_data.get('command_id'),
            "success": False,
            "message": None,
            "data": None,
        }
        command = command_data.get('command')
        kwargs = command_data.get('kwargs', {})

        try:
            # ======================================================================
            # Connection Commands
            # ======================================================================
            if command == 'connection_open':
                if 'settings' in kwargs and kwargs['settings'] is not None:
                    self.fptr.setSettings(json.dumps(kwargs['settings']))
                self._check_result(self.fptr.open(), "открытия соединения")
                response['success'] = True
                response['message'] = "Соединение с ККТ успешно установлено"

            elif command == 'connection_close':
                self._check_result(self.fptr.close(), "закрытия соединения")
                response['success'] = True
                response['message'] = "Соединение с ККТ закрыто"

            elif command == 'connection_is_opened':
                is_opened = self.fptr.isOpened()
                response['success'] = True
                response['message'] = "Соединение активно" if is_opened else "Соединение не установлено"
                response['data'] = {
                    'is_opened': is_opened,
                    'message': response['message']
                }

            # ======================================================================
            # Shift Commands
            # ======================================================================
            elif command == 'shift_open':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
                self._check_result(self.fptr.openShift(), "открытия смены")
                shift_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
                response['success'] = True
                response['message'] = f"Смена #{shift_number} успешно открыта"
                response['data'] = {'shift_number': shift_number}

            elif command == 'shift_close':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
                self._check_result(self.fptr.closeShift(), "закрытия смены")
                response['success'] = True
                response['data'] = {
                    "shift_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                    "fiscal_document_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
                }
                response['message'] = "Смена успешно закрыта, Z-отчет напечатан"

            # ======================================================================
            # Receipt Commands
            # ======================================================================
            elif command == 'receipt_open':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, kwargs['receipt_type'])
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
                if kwargs.get('customer_contact'):
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BUYER_EMAIL_OR_PHONE, kwargs['customer_contact'])
                self._check_result(self.fptr.openReceipt(), "открытия чека")
                response['success'] = True
                response['message'] = f"Чек типа {kwargs['receipt_type']} успешно открыт"

            elif command == 'receipt_add_item':
                for key, value in kwargs.items():
                    if key == 'name': self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, value)
                    elif key == 'price': self.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, value)
                    elif key == 'quantity': self.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, value)
                    elif key == 'tax_type': self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, value)
                    elif key == 'payment_method': self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE_SIGN, value)
                    elif key == 'payment_object': self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_SIGN, value)
                self._check_result(self.fptr.registration(), "регистрации позиции")
                response['success'] = True
                response['message'] = f"Позиция '{kwargs['name']}' добавлена"

            elif command == 'receipt_add_payment':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, kwargs['payment_type'])
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, kwargs['amount'])
                self._check_result(self.fptr.payment(), "регистрации оплаты")
                response['success'] = True
                response['message'] = f"Оплата {kwargs['amount']:.2f} добавлена"

            elif command == 'receipt_close':
                self._check_result(self.fptr.closeReceipt(), "закрытия чека")
                response['success'] = True
                response['data'] = {
                    "fiscal_document_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
                    "fiscal_document_sign": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
                    "shift_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                }
                response['message'] = "Чек успешно закрыт и напечатан"

            elif command == 'receipt_cancel':
                self._check_result(self.fptr.cancelReceipt(), "отмены чека")
                response['success'] = True
                response['message'] = "Чек отменен"

            # ======================================================================
            # Sound Commands
            # ======================================================================
            elif command == 'beep':
                frequency = kwargs.get('frequency', 2000)
                duration = kwargs.get('duration', 100)
                self._play_beep(frequency, duration)
                response['success'] = True
                response['message'] = f"Звуковой сигнал воспроизведен (частота: {frequency} Гц, длительность: {duration} мс)"

            elif command == 'play_arcane_melody':
                self._play_arcane_melody()
                response['success'] = True
                response['message'] = "Мелодия 'Enemy' из Arcane успешно воспроизведена!"

            # ======================================================================
            # Cash Commands
            # ======================================================================
            elif command == 'cash_income':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, kwargs['amount'])
                self._check_result(self.fptr.cashIncome(), "внесения наличных")
                response['success'] = True
                response['message'] = f"Внесено наличных: {kwargs['amount']:.2f}"

            elif command == 'cash_outcome':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, kwargs['amount'])
                self._check_result(self.fptr.cashOutcome(), "выплаты наличных")
                response['success'] = True
                response['message'] = f"Выплачено наличных: {kwargs['amount']:.2f}"

            # ======================================================================
            # Print Commands
            # ======================================================================
            elif command == 'print_text':
                text = kwargs.get('text', '')
                # Обязательные параметры
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, text)
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_LEFT))
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT_WRAP, kwargs.get('wrap', IFptr.LIBFPTR_TW_NONE))

                # Опциональные параметры
                if 'font' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT, kwargs['font'])
                if 'double_width' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_WIDTH, kwargs['double_width'])
                if 'double_height' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT, kwargs['double_height'])
                if 'linespacing' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_LINESPACING, kwargs['linespacing'])
                if 'brightness' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BRIGHTNESS, kwargs['brightness'])
                if 'defer' in kwargs and kwargs['defer'] != 0:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_DEFER, kwargs['defer'])

                self._check_result(self.fptr.printText(), "печати текста")
                response['success'] = True
                response['message'] = f"Текст напечатан: '{text}'"

            elif command == 'print_feed':
                lines = kwargs.get('lines', 1)
                for _ in range(lines):
                    self._check_result(self.fptr.printText(), "промотки ленты")
                response['success'] = True
                response['message'] = f"Промотано строк: {lines}"

            elif command == 'print_barcode':
                barcode = kwargs['barcode']
                # Обязательные параметры
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, barcode)
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, kwargs.get('barcode_type', IFptr.LIBFPTR_BT_QR))
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_LEFT))
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, kwargs.get('scale', 2))

                # Опциональные параметры
                if 'left_margin' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_LEFT_MARGIN, kwargs['left_margin'])
                if 'invert' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_INVERT, kwargs['invert'])
                if 'height' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_HEIGHT, kwargs['height'])
                if 'print_text' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_PRINT_TEXT, kwargs['print_text'])
                if 'correction' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_CORRECTION, kwargs['correction'])
                if 'version' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_VERSION, kwargs['version'])
                if 'columns' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_COLUMNS, kwargs['columns'])
                if 'defer' in kwargs and kwargs['defer'] != 0:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_DEFER, kwargs['defer'])

                self._check_result(self.fptr.printBarcode(), "печати штрихкода")
                response['success'] = True
                response['message'] = f"Штрихкод напечатан: '{barcode}'"

            elif command == 'print_picture':
                filename = kwargs['filename']
                # Обязательные параметры
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_FILENAME, filename)
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_LEFT))
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE_PERCENT, kwargs.get('scale_percent', 100))

                # Опциональные параметры
                if 'left_margin' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_LEFT_MARGIN, kwargs['left_margin'])

                self._check_result(self.fptr.printPicture(), "печати картинки")
                response['success'] = True
                response['message'] = f"Картинка напечатана: '{filename}'"

            elif command == 'print_picture_by_number':
                picture_number = kwargs['picture_number']
                # Обязательные параметры
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_PICTURE_NUMBER, picture_number)
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_LEFT))

                # Опциональные параметры
                if 'left_margin' in kwargs:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_LEFT_MARGIN, kwargs['left_margin'])
                if 'defer' in kwargs and kwargs['defer'] != 0:
                    self.fptr.setParam(IFptr.LIBFPTR_PARAM_DEFER, kwargs['defer'])

                self._check_result(self.fptr.printPictureByNumber(), "печати картинки из памяти")
                response['success'] = True
                response['message'] = f"Картинка №{picture_number} напечатана"

            elif command == 'print_x_report':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)
                self._check_result(self.fptr.report(), "печати X-отчета")
                response['success'] = True
                response['message'] = "X-отчет напечатан"

            elif command == 'open_cash_drawer':
                self._check_result(self.fptr.openCashDrawer(), "открытия денежного ящика")
                response['success'] = True
                response['message'] = "Денежный ящик открыт"

            elif command == 'cut_paper':
                self._check_result(self.fptr.cut(), "отрезания чека")
                response['success'] = True
                response['message'] = "Чек отрезан"

            # ======================================================================
            # Query Commands (All of them)
            # ======================================================================
            elif command == 'get_status':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
                self._check_result(self.fptr.queryData(), "запроса статуса")
                response['data'] = {
                    "model_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
                    "serial_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),
                    "shift_state": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
                    "cover_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
                    "paper_present": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
                }
                response['success'] = True

            elif command == 'get_short_status':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHORT_STATUS)
                self._check_result(self.fptr.queryData(), "короткого запроса статуса")
                response['data'] = {
                    "cashdrawer_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
                    "paper_present": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
                    "paper_near_end": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
                    "cover_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
                }
                response['success'] = True

            elif command == 'get_cash_sum':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASH_SUM)
                self._check_result(self.fptr.queryData(), "запроса суммы наличных")
                response['data'] = {"cash_sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}
                response['success'] = True

            elif command == 'get_shift_state':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
                self._check_result(self.fptr.queryData(), "запроса состояния смены")
                dt = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
                response['data'] = {
                    "shift_state": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
                    "shift_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                    "date_time": dt.isoformat() if isinstance(dt, datetime.datetime) else None,
                }
                response['success'] = True

            elif command == 'get_receipt_state':
                self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
                self._check_result(self.fptr.queryData(), "запроса состояния чека")
                response['data'] = {
                    "receipt_type": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
                    "receipt_sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
                }
                response['success'] = True

            else:
                response['message'] = f"Неизвестная команда: {command}"

        except Exception as e:
            error_msg = f"Ошибка при выполнении команды '{command}': {str(e)}"
            logger.error(error_msg)
            response["message"] = error_msg
            if isinstance(e, AtolDriverError):
                response['data'] = e.to_dict()

        return response

def listen_to_redis():
    """Подключение к Redis и обработка команд"""
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    pubsub = r.pubsub()
    channel = 'command_fr_channel'
    response_channel = f'{channel}_response'
    pubsub.subscribe(channel)

    # Создаем единственный экземпляр процессора команд
    processor = CommandProcessor()
    logger.info(f"✓ Процессор команд инициализирован")
    logger.info(f"🎧 Ожидание команд в канале '{channel}'...")

    for message in pubsub.listen():
        if message.get('type') == 'message':
            if message.get('data') == 'ping':
                continue
            try:
                command_data = json.loads(message.get('data'))
                logger.debug(f"Получена команда: {command_data}")
                response = processor.process_command(command_data)
                r.publish(response_channel, json.dumps(response, ensure_ascii=False))
                logger.debug(f"Ответ отправлен в канал '{response_channel}': {response}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга команды: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    logger.info("🚀 Запуск Redis Queue Worker для АТОЛ ККТ")
    listen_to_redis()