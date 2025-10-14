"""
Коды ошибок драйвера АТОЛ ККТ v.10
"""
from enum import IntEnum


class DriverErrorCode(IntEnum):
    """
    Коды ошибок драйвера АТОЛ

    Каждый метод драйвера возвращает индикатор результата:
    - 0: успешное выполнение
    - -1: ошибка (используйте errorCode() и errorDescription())
    """

    # Успех
    OK = 0  # Ошибок нет

    # Ошибки подключения (1-15)
    CONNECTION_DISABLED = 1  # Соединение не установлено
    NO_CONNECTION = 2  # Нет связи
    PORT_BUSY = 3  # Порт занят
    PORT_NOT_AVAILABLE = 4  # Порт недоступен
    INCORRECT_DATA = 5  # Некорректные данные от устройства
    INTERNAL = 6  # Внутренняя ошибка библиотеки
    UNSUPPORTED_CAST = 7  # Неподдерживаемое преобразование типа параметра
    NO_REQUIRED_PARAM = 8  # Не найден обязательный параметр
    INVALID_SETTINGS = 9  # Некорректные настройки
    NOT_CONFIGURED = 10  # Драйвер не настроен
    NOT_SUPPORTED = 11  # Не поддерживается в данной версии
    INVALID_MODE = 12  # Не поддерживается в данном режиме
    INVALID_PARAM = 13  # Нeкорректное значение параметра
    NOT_LOADED = 14  # Не удалось загрузить библиотеку
    UNKNOWN = 15  # Неизвестная ошибка

    # Ошибки операций (16-50)
    INVALID_SUM = 16  # Неверная цена (сумма)
    INVALID_QUANTITY = 17  # Неверное количество
    CASH_COUNTER_OVERFLOW = 18  # Переполнение счетчика наличности
    LAST_OPERATION_STORNO_DENIED = 19  # Невозможно сторно последней операции
    STORNO_BY_CODE_DENIED = 20  # Сторно по коду невозможно
    LAST_OPERATION_NOT_REPEATABLE = 21  # Невозможен повтор последней операции
    DISCOUNT_NOT_REPEATABLE = 22  # Повторная скидка на операцию невозможна
    DISCOUNT_DENIED = 23  # Невозможно начислить скидку/надбавку
    INVALID_COMMODITY_CODE = 24  # Неверный код товара
    INVALID_COMMODITY_BARCODE = 25  # Неверный штрихкод товара
    INVALID_COMMAND_FORMAT = 26  # Неверный формат команды
    INVALID_COMMAND_LENGTH = 27  # Неверная длина
    BLOCKED_IN_DATE_INPUT_MODE = 28  # ККТ заблокирована в режиме ввода даты
    NEED_DATE_ACCEPT = 29  # Требуется подтверждение ввода даты
    NO_MORE_DATA = 30  # Нет больше данных
    NO_ACCEPT_OR_CANCEL = 31  # Нет подтверждения или отмены продажи
    BLOCKED_BY_REPORT_INTERRUPTION = 32  # Отчет о закрытии смены прерван
    DISABLE_CASH_CONTROL_DENIED = 33  # Отключение контроля наличности невозможно
    MODE_BLOCKED = 34  # Вход в режим заблокирован
    CHECK_DATE_TIME = 35  # Проверьте дату и время
    DATE_TIME_LESS_THAN_FS = 36  # Дата/время меньше даты/времени последнего ФД
    CLOSE_ARCHIVE_DENIED = 37  # Невозможно закрыть архив
    COMMODITY_NOT_FOUND = 38  # Товар не найден
    WEIGHT_BARCODE_WITH_INVALID_QUANTITY = 39  # Весовой штрихкод с количеством <> 1.000
    RECEIPT_BUFFER_OVERFLOW = 40  # Переполнение буфера чека
    QUANTITY_TOO_FEW = 41  # Недостаточное количество товара
    STORNO_TOO_MUCH = 42  # Сторнируемое количество больше проданного
    BLOCKED_COMMODITY_NOT_FOUND = 43  # Товар не найден
    NO_PAPER = 44  # Нет бумаги
    COVER_OPENED = 45  # Открыта крышка
    PRINTER_FAULT = 46  # Нет связи с принтером чеков
    MECHANICAL_FAULT = 47  # Механическая ошибка печатающего устройства
    INVALID_RECEIPT_TYPE = 48  # Неверный тип чека
    INVALID_UNIT_TYPE = 49  # Недопустимое целевое устройство
    NO_MEMORY = 50  # Нет места в массиве картинок/штрихкодов

    # Ошибки изображений и платежей (51-70)
    PICTURE_NOT_FOUND = 51  # Неверный номер картинки/штрихкода
    NONCACH_PAYMENTS_TOO_MUCH = 52  # Сумма не наличных платежей превышает сумму чека
    RETURN_DENIED = 53  # Накопление меньше суммы возврата или аннулирования
    PAYMENTS_OVERFLOW = 54  # Переполнение суммы платежей
    BUSY = 55  # Предыдущая операция незавершена
    GSM = 56  # Ошибка GSM-модуля
    INVALID_DISCOUNT = 57  # Неверная величина скидки / надбавки
    OPERATION_AFTER_DISCOUNT_DENIED = 58  # Операция после скидки / надбавки невозможна
    INVALID_DEPARTMENT = 59  # Неверная секция
    INVALID_PAYMENT_TYPE = 60  # Неверный вид оплаты
    MULTIPLICATION_OVERFLOW = 61  # Переполнение при умножении
    DENIED_BY_SETTINGS = 62  # Операция запрещена в таблице настроек
    TOTAL_OVERFLOW = 63  # Переполнение итога чека
    DENIED_IN_ANNULATION_RECEIPT = 64  # Открыт чек аннулирования
    JOURNAL_OVERFLOW = 65  # Переполнение буфера ЭЖ
    NOT_FULLY_PAID = 66  # Чек оплачен не полностью
    DENIED_IN_RETURN_RECEIPT = 67  # Открыт чек возврата
    SHIFT_EXPIRED = 68  # Смена превысила 24 часа
    DENIED_IN_SELL_RECEIPT = 69  # Открыт чек продажи
    FISCAL_MEMORY_OVERFLOW = 70  # Переполнение ФП

    # Ошибки смены и настроек (71-99)
    INVALID_PASSWORD = 71  # Неверный пароль
    JOURNAL_BUSY = 72  # Идет обработка ЭЖ
    DENIED_IN_CLOSED_SHIFT = 73  # Смена закрыта
    INVALID_TABLE_NUMBER = 74  # Неверный номер таблицы
    INVALID_ROW_NUMBER = 75  # Неверный номер ряда
    INVALID_FIELD_NUMBER = 76  # Неверный номер поля
    INVALID_DATE_TIME = 77  # Неверная дата и/или время
    INVALID_STORNO_SUM = 78  # Неверная сумма сторно
    CHANGE_CALCULATION = 79  # Подсчет суммы сдачи невозможен
    NO_CASH = 80  # В ККТ нет денег для выплаты
    DENIED_IN_CLOSED_RECEIPT = 81  # Чек закрыт
    DENIED_IN_OPENED_RECEIPT = 82  # Чек открыт
    DENIED_IN_OPENED_SHIFT = 83  # Смена открыта
    SERIAL_NUMBER_ALREADY_ENTERED = 84  # Серийный номер / MAC-адрес уже задан
    TOO_MUCH_REREGISTRATIONS = 85  # Исчерпан лимит перерегистраций
    INVALID_SHIFT_NUMBER = 86  # Неверный номер смены
    INVALID_SERIAL_NUMBER = 87  # Недопустимый серийный номер ККТ
    INVALID_RNM_VATIN = 88  # Недопустимый РНМ и/или ИНН
    FISCAL_PRINTER_NOT_ACTIVATED = 89  # ККТ не зарегистрирована
    SERIAL_NUMBER_NOT_ENTERED = 90  # Не задан серийный номер
    NO_MORE_REPORTS = 91  # Нет отчетов
    MODE_NOT_ACTIVATED = 92  # Режим не активизирован
    RECORD_NOT_FOUND_IN_JOURNAL = 93  # Данные документа отсутствуют
    INVALID_LICENSE = 94  # Некорректный код защиты / лицензия
    NEED_FULL_RESET = 95  # Требуется выполнение общего гашения
    DENIED_BY_LICENSE = 96  # Команда не разрешена кодами защиты
    DISCOUNT_CANCELLATION_DENIED = 97  # Невозможна отмена скидки/надбавки
    CLOSE_RECEIPT_DENIED = 98  # Невозможно закрыть чек данным типом оплаты
    INVALID_ROUTE_NUMBER = 99  # Неверный номер маршрута

    # Ошибки тарифов и ФН (100-150)
    INVALID_START_ZONE_NUMBER = 100  # Неверный номер начальной зоны
    INVALID_END_ZONE_NUMBER = 101  # Неверный номер конечной зоны
    INVALID_RATE_TYPE = 102  # Неверный тип тарифа
    INVALID_RATE = 103  # Неверный тариф
    FISCAL_MODULE_EXCHANGE = 104  # Ошибка обмена с фискальным модулем
    NEED_TECHNICAL_SUPPORT = 105  # Необходимо провести профилактические работы
    SHIFT_NUMBERS_DID_NOT_MATCH = 106  # Неверные номера смен в ККТ и ФН
    DEVICE_NOT_FOUND = 107  # Нет устройства
    EXTERNAL_DEVICE_CONNECTION = 108  # Нет связи с внешним устройством
    DISPENSER_INVALID_STATE = 109  # Ошибочное состояние ТРК
    INVALID_POSITIONS_COUNT = 110  # Недопустимое кол-во позиций в чеке
    DISPENSER_INVALID_NUMBER = 111  # Ошибочный номер ТРК
    INVALID_DIVIDER = 112  # Неверный делитель
    FN_ACTIVATION_DENIED = 113  # Активация данного ФН невозможна
    PRINTER_OVERHEAT = 114  # Перегрев головки принтера
    FN_EXCHANGE = 115  # Ошибка обмена с ФН на уровне I2C
    FN_INVALID_FORMAT = 116  # Ошибка формата передачи ФН
    FN_INVALID_STATE = 117  # Неверное состояние ФН
    FN_FAULT = 118  # Неисправимая ошибка ФН
    FN_CRYPTO_FAULT = 119  # Ошибка КС ФН
    FN_EXPIRED = 120  # Закончен срок эксплуатации ФН
    FN_OVERFLOW = 121  # Архив ФН переполнен
    FN_INVALID_DATE_TIME = 122  # В ФН переданы неверная дата или время
    FN_NO_MORE_DATA = 123  # В ФН нет запрошенных данных
    FN_TOTAL_OVERFLOW = 124  # Переполнение ФН (итог чека)
    BUFFER_OVERFLOW = 125  # Буфер переполнен
    PRINT_SECOND_COPY_DENIED = 126  # Невозможно напечатать вторую фискальную копию
    NEED_RESET_JOURNAL = 127  # Требуется гашение ЭЖ
    TAX_SUM_TOO_MUCH = 128  # Некорректная сумма налога
    TAX_ON_LAST_OPERATION_DENIED = 129  # Начисление налога на последнюю операцию невозможно
    INVALID_FN_NUMBER = 130  # Неверный номер ФН
    TAX_CANCEL_DENIED = 131  # Сумма сторно налога больше зарегистрированного
    LOW_BATTERY = 132  # Недостаточно питания
    FN_INVALID_COMMAND = 133  # Некорректное значение параметров команды ФН
    FN_COMMAND_OVERFLOW = 134  # Превышение размеров TLV данных ФН
    FN_NO_TRANSPORT_CONNECTION = 135  # Нет транспортного соединения ФН
    FN_CRYPTO_HAS_EXPIRED = 136  # Исчерпан ресурс КС ФН
    FN_RESOURCE_HAS_EXPIRED = 137  # Ресурс хранения ФД исчерпан
    INVALID_MESSAGE_FROM_OFD = 138  # Сообщение от ОФД не может быть принято ФН
    FN_HAS_NOT_SEND_DOCUMENTS = 139  # В ФН есть неотправленные ФД
    FN_TIMEOUT = 140  # Исчерпан ресурс ожидания передачи сообщения в ФН
    FN_SHIFT_EXPIRED = 141  # Продолжительность смены ФН более 24 часов
    FN_INVALID_TIME_DIFFERENCE = 142  # Неверная разница во времени
    INVALID_TAXATION_TYPE = 143  # Некорректная СНО
    INVALID_TAX_TYPE = 144  # Недопустимый номер ставки налога
    INVALID_COMMODITY_PAYMENT_TYPE = 145  # Недопустимый тип оплаты товара
    INVALID_COMMODITY_CODE_TYPE = 146  # Недопустимый тип кода товара
    EXCISABLE_COMMODITY_DENIED = 147  # Недопустима регистрация подакцизного товара
    FISCAL_PROPERTY_WRITE = 148  # Ошибка программирования реквизита
    INVALID_COUNTER_TYPE = 149  # Неверный тип счетчика
    CUTTER_FAULT = 150  # Ошибка отрезчика

    # Ошибки отчетов и печати (151-200)
    REPORT_INTERRUPTED = 151  # Снятие отчета прервалось
    INVALID_LEFT_MARGIN = 152  # Недопустимое значение отступа слева
    INVALID_ALIGNMENT = 153  # Недопустимое значение выравнивания
    INVALID_TAX_MODE = 154  # Недопустимое значение режима работы с налогом
    FILE_NOT_FOUND = 155  # Файл не найден или неверный формат
    PICTURE_TOO_BIG = 156  # Размер картинки слишком большой
    INVALID_BARCODE_PARAMS = 157  # Не удалось сформировать штрихкод
    FISCAL_PROPERTY_DENIED = 158  # Неразрешенные реквизиты
    FN_INTERFACE = 159  # Ошибка интерфейса ФН
    DATA_DUPLICATE = 160  # Дублирование данных
    NO_REQUIRED_FISCAL_PROPERTY = 161  # Не указаны обязательные реквизиты
    FN_READ_DOCUMENT = 162  # Ошибка чтения документа из ФН
    FLOAT_OVERFLOW = 163  # Переполнение чисел с плавающей точкой
    INVALID_SETTING_VALUE = 164  # Неверное значение параметра ККТ
    HARD_FAULT = 165  # Внутренняя ошибка ККТ
    FN_NOT_FOUND = 166  # ФН не найден
    INVALID_AGENT_FISCAL_PROPERTY = 167  # Невозможно записать реквизит агента
    INVALID_FISCAL_PROPERTY_VALUE_1002_1056 = 168  # Недопустимое сочетание 1002 и 1056
    INVALID_FISCAL_PROPERTY_VALUE_1002_1017 = 169  # Недопустимое сочетание 1002 и 1017
    SCRIPT = 170  # Ошибка скриптового движка ККТ
    INVALID_USER_MEMORY_INDEX = 171  # Неверный номер пользовательской ячейки памяти
    NO_ACTIVE_OPERATOR = 172  # Кассир не зарегистрирован
    REGISTRATION_REPORT_INTERRUPTED = 173  # Отчет о регистрации ККТ прерван
    CLOSE_FN_REPORT_INTERRUPTED = 174  # Отчет о закрытии ФН прерван
    OPEN_SHIFT_REPORT_INTERRUPTED = 175  # Отчет об открытии смены прерван
    OFD_EXCHANGE_REPORT_INTERRUPTED = 176  # Отчет о состоянии расчетов прерван
    CLOSE_RECEIPT_INTERRUPTED = 177  # Закрытие чека прервано
    FN_QUERY_INTERRUPTED = 178  # Получение документа из ФН прервано
    RTC_FAULT = 179  # Сбой часов
    MEMORY_FAULT = 180  # Сбой памяти
    CHIP_FAULT = 181  # Сбой микросхемы
    TEMPLATES_CORRUPTED = 182  # Ошибка шаблонов документов
    INVALID_MAC_ADDRESS = 183  # Недопустимое значение MAC-адреса
    INVALID_SCRIPT_NUMBER = 184  # Неверный тип (номер) шаблона
    SCRIPTS_FAULT = 185  # Загруженные шаблоны повреждены или отсутствуют
    INVALID_SCRIPTS_VERSION = 186  # Несовместимая версия загруженных шаблонов
    INVALID_CLICHE_FORMAT = 187  # Ошибка в формате клише
    WAIT_FOR_REBOOT = 188  # Требуется перезагрузка ККТ
    NO_LICENSE = 189  # Подходящие лицензии не найдены
    INVALID_FFD_VERSION = 190  # Неверная версия ФФД
    CHANGE_SETTING_DENIED = 191  # Параметр доступен только для чтения
    INVALID_NOMENCLATURE_TYPE = 192  # Неверный тип кода товара
    INVALID_GTIN = 193  # Неверное значение GTIN
    NEGATIVE_MATH_RESULT = 194  # Отрицательный результат математической операции
    FISCAL_PROPERTIES_COMBINATION = 195  # Недопустимое сочетание реквизитов
    OPERATOR_LOGIN = 196  # Не удалось зарегистрировать кассира
    INVALID_INTERNET_CHANNEL = 197  # Данный канал Интернет отсутствует в ККТ
    DATETIME_NOT_SYNCRONIZED = 198  # Дата и время не синхронизированы
    JOURNAL = 199  # Ошибка электронного журнала
    DENIED_IN_OPENED_DOC = 200  # Документ открыт

    # Ошибки документов и лицензий (201-269)
    DENIED_IN_CLOSED_DOC = 201  # Документ закрыт
    LICENSE_MEMORY_OVERFLOW = 202  # Нет места для сохранения лицензий
    NEED_CANCEL_DOCUMENT = 203  # Документ необходимо отменить
    REGISTERS_NOT_INITIALIZED = 204  # Регистры ККТ еще не инициализированы
    TOTAL_REQUIRED = 205  # Требуется регистрация итога
    SETTINGS_FAULT = 206  # Сбой таблицы настроек
    COUNTERS_FAULT = 207  # Сбой счетчиков и регистров ККТ
    USER_MEMORY_FAULT = 208  # Сбой пользовательской памяти
    SERVICE_COUNTERS_FAULT = 209  # Сбой сервисных регистров
    ATTRIBUTES_FAULT = 210  # Сбой реквизитов ККТ
    ALREADY_IN_UPDATE_MODE = 211  # ККТ уже в режиме обновления конфигурации
    INVALID_FIRMWARE = 212  # Конфигурация не прошла проверку
    INVALID_CHANNEL = 213  # Аппаратный канал отсутствует
    INTERFACE_DOWN = 214  # Сетевой интерфейс не подключен
    INVALID_FISCAL_PROPERTY_VALUE_1212_1030 = 215  # Недопустимое сочетание 1212 и 1030
    INVALID_FISCAL_PROPERTY_VALUE_1214 = 216  # Некорректный признак способа расчета
    INVALID_FISCAL_PROPERTY_VALUE_1212 = 217  # Некорректный признак предмета расчета
    SYNC_TIME = 218  # Ошибка синхронизации времени
    VAT18_VAT20_IN_RECEIPT = 219  # В чеке не может быть НДС 18% и 20%
    PICTURE_NOT_CLOSED = 220  # Картинка не закрыта
    INTERFACE_BUSY = 221  # Сетевой интерфейс занят
    INVALID_PICTURE_NUMBER = 222  # Неверный номер картинки
    INVALID_CONTAINER = 223  # Ошибка проверки контейнера
    ARCHIVE_CLOSED = 224  # Архив ФН закрыт
    NEED_REGISTRATION = 225  # Нужно выполнить регистрацию
    DENIED_DURING_UPDATE = 226  # Идет обновление ПО ККТ
    INVALID_TOTAL = 227  # Неверный итог чека
    MARKING_CODE_CONFLICT = 228  # Запрещена одновременная передача КМ и 1162
    INVALID_RECORDS_ID = 229  # Набор записей не найден
    INVALID_SIGNATURE = 230  # Ошибка цифровой подписи
    INVALID_EXCISE_SUM = 231  # Некорректная сумма акциза
    NO_DOCUMENTS_FOUND_IN_JOURNAL = 232  # Документы не найдены в БД
    INVALID_SCRIPT_TYPE = 233  # Неподдерживаемый тип скрипта
    INVALID_SCRIPT_NAME = 234  # Некорректный идентификатор скрипта
    INVALID_POSITIONS_COUNT_WITH_1162 = 235  # Кол-во позиций с 1162/1163 превысило лимит
    INVALID_UC_COUNTER = 236  # Универсальный счетчик недоступен
    INVALID_UC_TAG = 237  # Неподдерживаемый тег для универсальных счетчиков
    INVALID_UC_IDX = 238  # Некорректный индекс для универсальных счетчиков
    INVALID_UC_SIZE = 239  # Неверный размер универсального счетчика
    INVALID_UC_CONFIG = 240  # Неверная конфигурация универсальных счетчиков
    CONNECTION_LOST = 241  # Соединение с ККТ потеряно
    UNIVERSAL_COUNTERS_FAULT = 242  # Ошибка универсальных счетчиков
    INVALID_TAX_SUM = 243  # Некорректная сумма налога
    INVALID_MARKING_CODE_TYPE = 244  # Некорректное значение типа КМ
    LICENSE_HARD_FAULT = 245  # Аппаратная ошибка при сохранении лицензии
    LICENSE_INVALID_SIGN = 246  # Подпись лицензии некорректна
    LICENSE_INVALID_SERIAL = 247  # Лицензия не подходит для данной ККТ
    LICENSE_INVALID_TIME = 248  # Срок действия лицензии истёк
    DOCUMENT_CANCELED = 249  # Документ был отменен
    INVALID_SCRIPT_PARAMS = 250  # Некорректные параметры скрипта
    CLICHE_TOO_LONG = 251  # Длина клише превышает максимальное значение
    COMMODITIES_TABLE_FAULT = 252  # Ошибка таблицы товаров
    COMMODITIES_TABLE = 253  # Общая ошибка таблицы товаров
    COMMODITIES_TABLE_INVALID_TAG = 254  # Некорректный тег для таблицы товаров
    COMMODITIES_TABLE_INVALID_TAG_SIZE = 255  # Некорректный размер тега
    COMMODITIES_TABLE_NO_TAG_DATA = 256  # Нет данных по тегу
    COMMODITIES_TABLE_NO_FREE_MEMORY = 257  # Нет места в таблице товаров
    INVALID_CACHE = 258  # Ошибка чтения/записи данных кеша
    SCHEDULER_NOT_READY = 259  # Функции планировщика не доступны
    SCHEDULER_INVALID_TASK = 260  # Неизвестный тип задания планировщика
    MINIPOS_NO_POSITION_PAYMENT = 261  # Отсутствует позиция оплаты
    MINIPOS_COMMAND_TIME_OUT = 262  # Таймаут выполнения команды истек
    MINIPOS_MODE_FR_DISABLED = 263  # Режим ФР выключен
    ENTRY_NOT_FOUND_IN_OTP = 264  # Не найдена запись в OTP
    EXCISABLE_COMMODITY_WITHOUT_EXCISE = 265  # Подакцизный товар без акциза
    BARCODE_TYPE_NOT_SUPPORTED = 266  # Тип штрихкода не поддерживается
    OVERLAY_DATA_OVERFLOW = 267  # Размер данных превышает допустимый
    INVALID_MODULE_ADDRESS = 268  # Ошибка чтения адреса модуля и сегмента
    ECR_MODEL_NOT_SUPPORTED = 269  # Данная модель ККТ не поддерживается

    # Ошибки маркировки (401-426)
    MARKING_CODE_VALIDATION_IN_PROGRESS = 401  # Процедура проверки КМ уже запущена
    NO_CONNECTION_WITH_SERVER = 402  # Ошибка соединения с сервером
    MARKING_CODE_VALIDATION_CANCELED = 403  # Процедура проверки КМ прервана
    INVALID_MARKING_CODE_STATUS = 404  # Некорректное значение статуса КМ
    INVALID_GS1 = 405  # Неверный код GS1
    MARKING_WORK_DENIED = 406  # Запрещена работа с маркированным товарами
    MARKING_WORK_TEMPORARY_BLOCKED = 407  # Работа с маркированными товарами временно заблокирована
    MARKS_OVERFLOW = 408  # Переполнена таблица хранения КМ
    INVALID_MARKING_CODE = 409  # Некорректный код маркировки
    INVALID_STATE = 410  # Неверное состояние
    OFD_EXCHANGE = 411  # Ошибка обмена с сервером ОФД или ИСМ
    INVALID_MEASUREMENT_UNIT = 412  # Некорректное значение единиц измерения
    OPERATION_DENIED_IN_CURRENT_FFD = 413  # Операция не разрешена в данной версии ФФД
    MARKING_OPERATION_DENIED = 414  # Операция не разрешена
    NO_DATA_TO_SEND = 415  # Нет данных для отправки
    NO_MARKED_POSITION = 416  # Нет маркированных позиций в чеке
    HAS_NOT_SEND_NOTICES = 417  # Имеются неотправленные уведомления
    UPDATE_KEYS_REQUIRED = 418  # Требуется повторное обновление ключей
    UPDATE_KEYS_SERVICE = 419  # Ошибка сервиса обновления ключей
    MARK_NOT_CHECKED = 420  # КМ не проверен в ФН
    MARK_CHECK_TIMEOUT_EXPIRED = 421  # Истёк таймаут проверки КМ
    NO_MARKING_CODE_IN_TABLE = 422  # КМ отсутствует в таблице
    CHEKING_MARK_IN_PROGRESS = 423  # Выполняется проверка КМ
    INVALID_SERVER_ADDRESS = 424  # Настройки адреса сервера не заданы
    UPDATE_KEYS_TIMEOUT = 425  # Истёк таймаут обновления ключей
    PROPERTY_FOR_MARKING_POSITION_ONLY = 426  # Реквизит только для маркированной позиции

    # Ошибки скриптов (501-504)
    RECEIPT_PARSE_ERROR = 501  # Ошибка парсинга запроса
    INTERRUPTED_BY_PREVIOUS_ERRORS = 502  # Выполнение прервано из-за предыдущих ошибок
    DRIVER_SCRIPT_ERROR = 503  # Ошибка скрипта драйвера
    VALIDATE_FUNC_NOT_FOUND = 504  # Функция проверки задания не найдена

    # Ошибки удалённого подключения (601-603)
    RCP_SERVER_BUSY = 601  # Устройство занято другим клиентом
    RCP_SERVER_VERSION = 602  # Некорректная версия протокола
    RCP_SERVER_EXCHANGE = 603  # Ошибка обмена с сервером

    # Пользовательские ошибки скриптов (1000-1999)
    # USERS_SCRIPTS_BASE = 1000
    # USERS_SCRIPTS_END = 1999


# Словарь сообщений об ошибках
ERROR_MESSAGES = {
    DriverErrorCode.OK: "Ошибок нет",
    DriverErrorCode.CONNECTION_DISABLED: "Соединение не установлено",
    DriverErrorCode.NO_CONNECTION: "Нет связи",
    DriverErrorCode.PORT_BUSY: "Порт занят",
    DriverErrorCode.PORT_NOT_AVAILABLE: "Порт недоступен",
    DriverErrorCode.INCORRECT_DATA: "Некорректные данные от устройства",
    DriverErrorCode.INTERNAL: "Внутренняя ошибка библиотеки",
    DriverErrorCode.UNSUPPORTED_CAST: "Неподдерживаемое преобразование типа параметра",
    DriverErrorCode.NO_REQUIRED_PARAM: "Не найден обязательный параметр",
    DriverErrorCode.INVALID_SETTINGS: "Некорректные настройки",
    DriverErrorCode.NOT_CONFIGURED: "Драйвер не настроен",
    DriverErrorCode.NOT_SUPPORTED: "Не поддерживается в данной версии",
    DriverErrorCode.INVALID_MODE: "Не поддерживается в данном режиме",
    DriverErrorCode.INVALID_PARAM: "Некорректное значение параметра",
    DriverErrorCode.NOT_LOADED: "Не удалось загрузить библиотеку",
    DriverErrorCode.UNKNOWN: "Неизвестная ошибка",
    DriverErrorCode.CONNECTION_LOST: "Соединение с ККТ потеряно",
    # ... остальные можно добавлять по необходимости
}


def get_error_message(code: int) -> str:
    """
    Получить сообщение об ошибке по коду

    Args:
        code: Код ошибки

    Returns:
        str: Сообщение об ошибке
    """
    try:
        error_code = DriverErrorCode(code)
        return ERROR_MESSAGES.get(error_code, f"Ошибка {code}")
    except ValueError:
        return f"Неизвестная ошибка {code}"
