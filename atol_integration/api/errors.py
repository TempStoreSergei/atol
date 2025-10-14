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


# Словарь сообщений об ошибках (полный список 000-603)
ERROR_MESSAGES = {
    code: code.name.replace('_', ' ').title() for code in DriverErrorCode
}

# Переопределяем с полными русскими описаниями (все 269 кодов)
ERROR_MESSAGES.update({
    # Успех
    DriverErrorCode.OK: "Ошибок нет",

    # Ошибки подключения (1-15)
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

    # Ошибки операций (16-50)
    DriverErrorCode.INVALID_SUM: "Неверная цена (сумма)",
    DriverErrorCode.INVALID_QUANTITY: "Неверное количество",
    DriverErrorCode.CASH_COUNTER_OVERFLOW: "Переполнение счетчика наличности",
    DriverErrorCode.LAST_OPERATION_STORNO_DENIED: "Невозможно сторно последней операции",
    DriverErrorCode.STORNO_BY_CODE_DENIED: "Сторно по коду невозможно",
    DriverErrorCode.LAST_OPERATION_NOT_REPEATABLE: "Невозможен повтор последней операции",
    DriverErrorCode.DISCOUNT_NOT_REPEATABLE: "Повторная скидка на операцию невозможна",
    DriverErrorCode.DISCOUNT_DENIED: "Невозможно начислить скидку/надбавку",
    DriverErrorCode.INVALID_COMMODITY_CODE: "Неверный код товара",
    DriverErrorCode.INVALID_COMMODITY_BARCODE: "Неверный штрихкод товара",
    DriverErrorCode.INVALID_COMMAND_FORMAT: "Неверный формат команды",
    DriverErrorCode.INVALID_COMMAND_LENGTH: "Неверная длина",
    DriverErrorCode.BLOCKED_IN_DATE_INPUT_MODE: "ККТ заблокирована в режиме ввода даты",
    DriverErrorCode.NEED_DATE_ACCEPT: "Требуется подтверждение ввода даты",
    DriverErrorCode.NO_MORE_DATA: "Нет больше данных",
    DriverErrorCode.NO_ACCEPT_OR_CANCEL: "Нет подтверждения или отмены продажи",
    DriverErrorCode.BLOCKED_BY_REPORT_INTERRUPTION: "Отчет о закрытии смены прерван",
    DriverErrorCode.DISABLE_CASH_CONTROL_DENIED: "Отключение контроля наличности невозможно",
    DriverErrorCode.MODE_BLOCKED: "Вход в режим заблокирован",
    DriverErrorCode.CHECK_DATE_TIME: "Проверьте дату и время",
    DriverErrorCode.DATE_TIME_LESS_THAN_FS: "Дата/время меньше даты/времени последнего ФД",
    DriverErrorCode.CLOSE_ARCHIVE_DENIED: "Невозможно закрыть архив",
    DriverErrorCode.COMMODITY_NOT_FOUND: "Товар не найден",
    DriverErrorCode.WEIGHT_BARCODE_WITH_INVALID_QUANTITY: "Весовой штрихкод с количеством <> 1.000",
    DriverErrorCode.RECEIPT_BUFFER_OVERFLOW: "Переполнение буфера чека",
    DriverErrorCode.QUANTITY_TOO_FEW: "Недостаточное количество товара",
    DriverErrorCode.STORNO_TOO_MUCH: "Сторнируемое количество больше проданного",
    DriverErrorCode.BLOCKED_COMMODITY_NOT_FOUND: "Товар не найден",
    DriverErrorCode.NO_PAPER: "Нет бумаги",
    DriverErrorCode.COVER_OPENED: "Открыта крышка",
    DriverErrorCode.PRINTER_FAULT: "Нет связи с принтером чеков",
    DriverErrorCode.MECHANICAL_FAULT: "Механическая ошибка печатающего устройства",
    DriverErrorCode.INVALID_RECEIPT_TYPE: "Неверный тип чека",
    DriverErrorCode.INVALID_UNIT_TYPE: "Недопустимое целевое устройство",
    DriverErrorCode.NO_MEMORY: "Нет места в массиве картинок/штрихкодов",

    # Ошибки изображений и платежей (51-70)
    DriverErrorCode.PICTURE_NOT_FOUND: "Неверный номер картинки/штрихкода",
    DriverErrorCode.NONCACH_PAYMENTS_TOO_MUCH: "Сумма не наличных платежей превышает сумму чека",
    DriverErrorCode.RETURN_DENIED: "Накопление меньше суммы возврата или аннулирования",
    DriverErrorCode.PAYMENTS_OVERFLOW: "Переполнение суммы платежей",
    DriverErrorCode.BUSY: "Предыдущая операция незавершена",
    DriverErrorCode.GSM: "Ошибка GSM-модуля",
    DriverErrorCode.INVALID_DISCOUNT: "Неверная величина скидки / надбавки",
    DriverErrorCode.OPERATION_AFTER_DISCOUNT_DENIED: "Операция после скидки / надбавки невозможна",
    DriverErrorCode.INVALID_DEPARTMENT: "Неверная секция",
    DriverErrorCode.INVALID_PAYMENT_TYPE: "Неверный вид оплаты",
    DriverErrorCode.MULTIPLICATION_OVERFLOW: "Переполнение при умножении",
    DriverErrorCode.DENIED_BY_SETTINGS: "Операция запрещена в таблице настроек",
    DriverErrorCode.TOTAL_OVERFLOW: "Переполнение итога чека",
    DriverErrorCode.DENIED_IN_ANNULATION_RECEIPT: "Открыт чек аннулирования",
    DriverErrorCode.JOURNAL_OVERFLOW: "Переполнение буфера ЭЖ",
    DriverErrorCode.NOT_FULLY_PAID: "Чек оплачен не полностью",
    DriverErrorCode.DENIED_IN_RETURN_RECEIPT: "Открыт чек возврата",
    DriverErrorCode.SHIFT_EXPIRED: "Смена превысила 24 часа",
    DriverErrorCode.DENIED_IN_SELL_RECEIPT: "Открыт чек продажи",
    DriverErrorCode.FISCAL_MEMORY_OVERFLOW: "Переполнение ФП",

    # Ошибки смены и настроек (71-99)
    DriverErrorCode.INVALID_PASSWORD: "Неверный пароль",
    DriverErrorCode.JOURNAL_BUSY: "Идет обработка ЭЖ",
    DriverErrorCode.DENIED_IN_CLOSED_SHIFT: "Смена закрыта",
    DriverErrorCode.INVALID_TABLE_NUMBER: "Неверный номер таблицы",
    DriverErrorCode.INVALID_ROW_NUMBER: "Неверный номер ряда",
    DriverErrorCode.INVALID_FIELD_NUMBER: "Неверный номер поля",
    DriverErrorCode.INVALID_DATE_TIME: "Неверная дата и/или время",
    DriverErrorCode.INVALID_STORNO_SUM: "Неверная сумма сторно",
    DriverErrorCode.CHANGE_CALCULATION: "Подсчет суммы сдачи невозможен",
    DriverErrorCode.NO_CASH: "В ККТ нет денег для выплаты",
    DriverErrorCode.DENIED_IN_CLOSED_RECEIPT: "Чек закрыт",
    DriverErrorCode.DENIED_IN_OPENED_RECEIPT: "Чек открыт",
    DriverErrorCode.DENIED_IN_OPENED_SHIFT: "Смена открыта",
    DriverErrorCode.SERIAL_NUMBER_ALREADY_ENTERED: "Серийный номер / MAC-адрес уже задан",
    DriverErrorCode.TOO_MUCH_REREGISTRATIONS: "Исчерпан лимит перерегистраций",
    DriverErrorCode.INVALID_SHIFT_NUMBER: "Неверный номер смены",
    DriverErrorCode.INVALID_SERIAL_NUMBER: "Недопустимый серийный номер ККТ",
    DriverErrorCode.INVALID_RNM_VATIN: "Недопустимый РНМ и/или ИНН",
    DriverErrorCode.FISCAL_PRINTER_NOT_ACTIVATED: "ККТ не зарегистрирована",
    DriverErrorCode.SERIAL_NUMBER_NOT_ENTERED: "Не задан серийный номер",
    DriverErrorCode.NO_MORE_REPORTS: "Нет отчетов",
    DriverErrorCode.MODE_NOT_ACTIVATED: "Режим не активизирован",
    DriverErrorCode.RECORD_NOT_FOUND_IN_JOURNAL: "Данные документа отсутствуют",
    DriverErrorCode.INVALID_LICENSE: "Некорректный код защиты / лицензия",
    DriverErrorCode.NEED_FULL_RESET: "Требуется выполнение общего гашения",
    DriverErrorCode.DENIED_BY_LICENSE: "Команда не разрешена кодами защиты",
    DriverErrorCode.DISCOUNT_CANCELLATION_DENIED: "Невозможна отмена скидки/надбавки",
    DriverErrorCode.CLOSE_RECEIPT_DENIED: "Невозможно закрыть чек данным типом оплаты",
    DriverErrorCode.INVALID_ROUTE_NUMBER: "Неверный номер маршрута",

    # Ошибки тарифов и ФН (100-150)
    DriverErrorCode.INVALID_START_ZONE_NUMBER: "Неверный номер начальной зоны",
    DriverErrorCode.INVALID_END_ZONE_NUMBER: "Неверный номер конечной зоны",
    DriverErrorCode.INVALID_RATE_TYPE: "Неверный тип тарифа",
    DriverErrorCode.INVALID_RATE: "Неверный тариф",
    DriverErrorCode.FISCAL_MODULE_EXCHANGE: "Ошибка обмена с фискальным модулем",
    DriverErrorCode.NEED_TECHNICAL_SUPPORT: "Необходимо провести профилактические работы",
    DriverErrorCode.SHIFT_NUMBERS_DID_NOT_MATCH: "Неверные номера смен в ККТ и ФН",
    DriverErrorCode.DEVICE_NOT_FOUND: "Нет устройства",
    DriverErrorCode.EXTERNAL_DEVICE_CONNECTION: "Нет связи с внешним устройством",
    DriverErrorCode.DISPENSER_INVALID_STATE: "Ошибочное состояние ТРК",
    DriverErrorCode.INVALID_POSITIONS_COUNT: "Недопустимое кол-во позиций в чеке",
    DriverErrorCode.DISPENSER_INVALID_NUMBER: "Ошибочный номер ТРК",
    DriverErrorCode.INVALID_DIVIDER: "Неверный делитель",
    DriverErrorCode.FN_ACTIVATION_DENIED: "Активация данного ФН невозможна",
    DriverErrorCode.PRINTER_OVERHEAT: "Перегрев головки принтера",
    DriverErrorCode.FN_EXCHANGE: "Ошибка обмена с ФН на уровне I2C",
    DriverErrorCode.FN_INVALID_FORMAT: "Ошибка формата передачи ФН",
    DriverErrorCode.FN_INVALID_STATE: "Неверное состояние ФН",
    DriverErrorCode.FN_FAULT: "Неисправимая ошибка ФН",
    DriverErrorCode.FN_CRYPTO_FAULT: "Ошибка КС ФН",
    DriverErrorCode.FN_EXPIRED: "Закончен срок эксплуатации ФН",
    DriverErrorCode.FN_OVERFLOW: "Архив ФН переполнен",
    DriverErrorCode.FN_INVALID_DATE_TIME: "В ФН переданы неверная дата или время",
    DriverErrorCode.FN_NO_MORE_DATA: "В ФН нет запрошенных данных",
    DriverErrorCode.FN_TOTAL_OVERFLOW: "Переполнение ФН (итог чека)",
    DriverErrorCode.BUFFER_OVERFLOW: "Буфер переполнен",
    DriverErrorCode.PRINT_SECOND_COPY_DENIED: "Невозможно напечатать вторую фискальную копию",
    DriverErrorCode.NEED_RESET_JOURNAL: "Требуется гашение ЭЖ",
    DriverErrorCode.TAX_SUM_TOO_MUCH: "Некорректная сумма налога",
    DriverErrorCode.TAX_ON_LAST_OPERATION_DENIED: "Начисление налога на последнюю операцию невозможно",
    DriverErrorCode.INVALID_FN_NUMBER: "Неверный номер ФН",
    DriverErrorCode.TAX_CANCEL_DENIED: "Сумма сторно налога больше зарегистрированного",
    DriverErrorCode.LOW_BATTERY: "Недостаточно питания",
    DriverErrorCode.FN_INVALID_COMMAND: "Некорректное значение параметров команды ФН",
    DriverErrorCode.FN_COMMAND_OVERFLOW: "Превышение размеров TLV данных ФН",
    DriverErrorCode.FN_NO_TRANSPORT_CONNECTION: "Нет транспортного соединения ФН",
    DriverErrorCode.FN_CRYPTO_HAS_EXPIRED: "Исчерпан ресурс КС ФН",
    DriverErrorCode.FN_RESOURCE_HAS_EXPIRED: "Ресурс хранения ФД исчерпан",
    DriverErrorCode.INVALID_MESSAGE_FROM_OFD: "Сообщение от ОФД не может быть принято ФН",
    DriverErrorCode.FN_HAS_NOT_SEND_DOCUMENTS: "В ФН есть неотправленные ФД",
    DriverErrorCode.FN_TIMEOUT: "Исчерпан ресурс ожидания передачи сообщения в ФН",
    DriverErrorCode.FN_SHIFT_EXPIRED: "Продолжительность смены ФН более 24 часов",
    DriverErrorCode.FN_INVALID_TIME_DIFFERENCE: "Неверная разница во времени",
    DriverErrorCode.INVALID_TAXATION_TYPE: "Некорректная СНО",
    DriverErrorCode.INVALID_TAX_TYPE: "Недопустимый номер ставки налога",
    DriverErrorCode.INVALID_COMMODITY_PAYMENT_TYPE: "Недопустимый тип оплаты товара",
    DriverErrorCode.INVALID_COMMODITY_CODE_TYPE: "Недопустимый тип кода товара",
    DriverErrorCode.EXCISABLE_COMMODITY_DENIED: "Недопустима регистрация подакцизного товара",
    DriverErrorCode.FISCAL_PROPERTY_WRITE: "Ошибка программирования реквизита",
    DriverErrorCode.INVALID_COUNTER_TYPE: "Неверный тип счетчика",
    DriverErrorCode.CUTTER_FAULT: "Ошибка отрезчика",

    # Ошибки отчетов и печати (151-200)
    DriverErrorCode.REPORT_INTERRUPTED: "Снятие отчета прервалось",
    DriverErrorCode.INVALID_LEFT_MARGIN: "Недопустимое значение отступа слева",
    DriverErrorCode.INVALID_ALIGNMENT: "Недопустимое значение выравнивания",
    DriverErrorCode.INVALID_TAX_MODE: "Недопустимое значение режима работы с налогом",
    DriverErrorCode.FILE_NOT_FOUND: "Файл не найден или неверный формат",
    DriverErrorCode.PICTURE_TOO_BIG: "Размер картинки слишком большой",
    DriverErrorCode.INVALID_BARCODE_PARAMS: "Не удалось сформировать штрихкод",
    DriverErrorCode.FISCAL_PROPERTY_DENIED: "Неразрешенные реквизиты",
    DriverErrorCode.FN_INTERFACE: "Ошибка интерфейса ФН",
    DriverErrorCode.DATA_DUPLICATE: "Дублирование данных",
    DriverErrorCode.NO_REQUIRED_FISCAL_PROPERTY: "Не указаны обязательные реквизиты",
    DriverErrorCode.FN_READ_DOCUMENT: "Ошибка чтения документа из ФН",
    DriverErrorCode.FLOAT_OVERFLOW: "Переполнение чисел с плавающей точкой",
    DriverErrorCode.INVALID_SETTING_VALUE: "Неверное значение параметра ККТ",
    DriverErrorCode.HARD_FAULT: "Внутренняя ошибка ККТ",
    DriverErrorCode.FN_NOT_FOUND: "ФН не найден",
    DriverErrorCode.INVALID_AGENT_FISCAL_PROPERTY: "Невозможно записать реквизит агента",
    DriverErrorCode.INVALID_FISCAL_PROPERTY_VALUE_1002_1056: "Недопустимое сочетание 1002 и 1056",
    DriverErrorCode.INVALID_FISCAL_PROPERTY_VALUE_1002_1017: "Недопустимое сочетание 1002 и 1017",
    DriverErrorCode.SCRIPT: "Ошибка скриптового движка ККТ",
    DriverErrorCode.INVALID_USER_MEMORY_INDEX: "Неверный номер пользовательской ячейки памяти",
    DriverErrorCode.NO_ACTIVE_OPERATOR: "Кассир не зарегистрирован",
    DriverErrorCode.REGISTRATION_REPORT_INTERRUPTED: "Отчет о регистрации ККТ прерван",
    DriverErrorCode.CLOSE_FN_REPORT_INTERRUPTED: "Отчет о закрытии ФН прерван",
    DriverErrorCode.OPEN_SHIFT_REPORT_INTERRUPTED: "Отчет об открытии смены прерван",
    DriverErrorCode.OFD_EXCHANGE_REPORT_INTERRUPTED: "Отчет о состоянии расчетов прерван",
    DriverErrorCode.CLOSE_RECEIPT_INTERRUPTED: "Закрытие чека прервано",
    DriverErrorCode.FN_QUERY_INTERRUPTED: "Получение документа из ФН прервано",
    DriverErrorCode.RTC_FAULT: "Сбой часов",
    DriverErrorCode.MEMORY_FAULT: "Сбой памяти",
    DriverErrorCode.CHIP_FAULT: "Сбой микросхемы",
    DriverErrorCode.TEMPLATES_CORRUPTED: "Ошибка шаблонов документов",
    DriverErrorCode.INVALID_MAC_ADDRESS: "Недопустимое значение MAC-адреса",
    DriverErrorCode.INVALID_SCRIPT_NUMBER: "Неверный тип (номер) шаблона",
    DriverErrorCode.SCRIPTS_FAULT: "Загруженные шаблоны повреждены или отсутствуют",
    DriverErrorCode.INVALID_SCRIPTS_VERSION: "Несовместимая версия загруженных шаблонов",
    DriverErrorCode.INVALID_CLICHE_FORMAT: "Ошибка в формате клише",
    DriverErrorCode.WAIT_FOR_REBOOT: "Требуется перезагрузка ККТ",
    DriverErrorCode.NO_LICENSE: "Подходящие лицензии не найдены",
    DriverErrorCode.INVALID_FFD_VERSION: "Неверная версия ФФД",
    DriverErrorCode.CHANGE_SETTING_DENIED: "Параметр доступен только для чтения",
    DriverErrorCode.INVALID_NOMENCLATURE_TYPE: "Неверный тип кода товара",
    DriverErrorCode.INVALID_GTIN: "Неверное значение GTIN",
    DriverErrorCode.NEGATIVE_MATH_RESULT: "Отрицательный результат математической операции",
    DriverErrorCode.FISCAL_PROPERTIES_COMBINATION: "Недопустимое сочетание реквизитов",
    DriverErrorCode.OPERATOR_LOGIN: "Не удалось зарегистрировать кассира",
    DriverErrorCode.INVALID_INTERNET_CHANNEL: "Данный канал Интернет отсутствует в ККТ",
    DriverErrorCode.DATETIME_NOT_SYNCRONIZED: "Дата и время не синхронизированы",
    DriverErrorCode.JOURNAL: "Ошибка электронного журнала",
    DriverErrorCode.DENIED_IN_OPENED_DOC: "Документ открыт",

    # Ошибки документов и лицензий (201-269)
    DriverErrorCode.DENIED_IN_CLOSED_DOC: "Документ закрыт",
    DriverErrorCode.LICENSE_MEMORY_OVERFLOW: "Нет места для сохранения лицензий",
    DriverErrorCode.NEED_CANCEL_DOCUMENT: "Документ необходимо отменить",
    DriverErrorCode.REGISTERS_NOT_INITIALIZED: "Регистры ККТ еще не инициализированы",
    DriverErrorCode.TOTAL_REQUIRED: "Требуется регистрация итога",
    DriverErrorCode.SETTINGS_FAULT: "Сбой таблицы настроек",
    DriverErrorCode.COUNTERS_FAULT: "Сбой счетчиков и регистров ККТ",
    DriverErrorCode.USER_MEMORY_FAULT: "Сбой пользовательской памяти",
    DriverErrorCode.SERVICE_COUNTERS_FAULT: "Сбой сервисных регистров",
    DriverErrorCode.ATTRIBUTES_FAULT: "Сбой реквизитов ККТ",
    DriverErrorCode.ALREADY_IN_UPDATE_MODE: "ККТ уже в режиме обновления конфигурации",
    DriverErrorCode.INVALID_FIRMWARE: "Конфигурация не прошла проверку",
    DriverErrorCode.INVALID_CHANNEL: "Аппаратный канал отсутствует",
    DriverErrorCode.INTERFACE_DOWN: "Сетевой интерфейс не подключен",
    DriverErrorCode.INVALID_FISCAL_PROPERTY_VALUE_1212_1030: "Недопустимое сочетание 1212 и 1030",
    DriverErrorCode.INVALID_FISCAL_PROPERTY_VALUE_1214: "Некорректный признак способа расчета",
    DriverErrorCode.INVALID_FISCAL_PROPERTY_VALUE_1212: "Некорректный признак предмета расчета",
    DriverErrorCode.SYNC_TIME: "Ошибка синхронизации времени",
    DriverErrorCode.VAT18_VAT20_IN_RECEIPT: "В чеке не может быть НДС 18% и 20%",
    DriverErrorCode.PICTURE_NOT_CLOSED: "Картинка не закрыта",
    DriverErrorCode.INTERFACE_BUSY: "Сетевой интерфейс занят",
    DriverErrorCode.INVALID_PICTURE_NUMBER: "Неверный номер картинки",
    DriverErrorCode.INVALID_CONTAINER: "Ошибка проверки контейнера",
    DriverErrorCode.ARCHIVE_CLOSED: "Архив ФН закрыт",
    DriverErrorCode.NEED_REGISTRATION: "Нужно выполнить регистрацию",
    DriverErrorCode.DENIED_DURING_UPDATE: "Идет обновление ПО ККТ",
    DriverErrorCode.INVALID_TOTAL: "Неверный итог чека",
    DriverErrorCode.MARKING_CODE_CONFLICT: "Запрещена одновременная передача КМ и 1162",
    DriverErrorCode.INVALID_RECORDS_ID: "Набор записей не найден",
    DriverErrorCode.INVALID_SIGNATURE: "Ошибка цифровой подписи",
    DriverErrorCode.INVALID_EXCISE_SUM: "Некорректная сумма акциза",
    DriverErrorCode.NO_DOCUMENTS_FOUND_IN_JOURNAL: "Документы не найдены в БД",
    DriverErrorCode.INVALID_SCRIPT_TYPE: "Неподдерживаемый тип скрипта",
    DriverErrorCode.INVALID_SCRIPT_NAME: "Некорректный идентификатор скрипта",
    DriverErrorCode.INVALID_POSITIONS_COUNT_WITH_1162: "Кол-во позиций с 1162/1163 превысило лимит",
    DriverErrorCode.INVALID_UC_COUNTER: "Универсальный счетчик недоступен",
    DriverErrorCode.INVALID_UC_TAG: "Неподдерживаемый тег для универсальных счетчиков",
    DriverErrorCode.INVALID_UC_IDX: "Некорректный индекс для универсальных счетчиков",
    DriverErrorCode.INVALID_UC_SIZE: "Неверный размер универсального счетчика",
    DriverErrorCode.INVALID_UC_CONFIG: "Неверная конфигурация универсальных счетчиков",
    DriverErrorCode.CONNECTION_LOST: "Соединение с ККТ потеряно",
    DriverErrorCode.UNIVERSAL_COUNTERS_FAULT: "Ошибка универсальных счетчиков",
    DriverErrorCode.INVALID_TAX_SUM: "Некорректная сумма налога",
    DriverErrorCode.INVALID_MARKING_CODE_TYPE: "Некорректное значение типа КМ",
    DriverErrorCode.LICENSE_HARD_FAULT: "Аппаратная ошибка при сохранении лицензии",
    DriverErrorCode.LICENSE_INVALID_SIGN: "Подпись лицензии некорректна",
    DriverErrorCode.LICENSE_INVALID_SERIAL: "Лицензия не подходит для данной ККТ",
    DriverErrorCode.LICENSE_INVALID_TIME: "Срок действия лицензии истёк",
    DriverErrorCode.DOCUMENT_CANCELED: "Документ был отменен",
    DriverErrorCode.INVALID_SCRIPT_PARAMS: "Некорректные параметры скрипта",
    DriverErrorCode.CLICHE_TOO_LONG: "Длина клише превышает максимальное значение",
    DriverErrorCode.COMMODITIES_TABLE_FAULT: "Ошибка таблицы товаров",
    DriverErrorCode.COMMODITIES_TABLE: "Общая ошибка таблицы товаров",
    DriverErrorCode.COMMODITIES_TABLE_INVALID_TAG: "Некорректный тег для таблицы товаров",
    DriverErrorCode.COMMODITIES_TABLE_INVALID_TAG_SIZE: "Некорректный размер тега",
    DriverErrorCode.COMMODITIES_TABLE_NO_TAG_DATA: "Нет данных по тегу",
    DriverErrorCode.COMMODITIES_TABLE_NO_FREE_MEMORY: "Нет места в таблице товаров",
    DriverErrorCode.INVALID_CACHE: "Ошибка чтения/записи данных кеша",
    DriverErrorCode.SCHEDULER_NOT_READY: "Функции планировщика не доступны",
    DriverErrorCode.SCHEDULER_INVALID_TASK: "Неизвестный тип задания планировщика",
    DriverErrorCode.MINIPOS_NO_POSITION_PAYMENT: "Отсутствует позиция оплаты",
    DriverErrorCode.MINIPOS_COMMAND_TIME_OUT: "Таймаут выполнения команды истек",
    DriverErrorCode.MINIPOS_MODE_FR_DISABLED: "Режим ФР выключен",
    DriverErrorCode.ENTRY_NOT_FOUND_IN_OTP: "Не найдена запись в OTP",
    DriverErrorCode.EXCISABLE_COMMODITY_WITHOUT_EXCISE: "Подакцизный товар без акциза",
    DriverErrorCode.BARCODE_TYPE_NOT_SUPPORTED: "Тип штрихкода не поддерживается",
    DriverErrorCode.OVERLAY_DATA_OVERFLOW: "Размер данных превышает допустимый",
    DriverErrorCode.INVALID_MODULE_ADDRESS: "Ошибка чтения адреса модуля и сегмента",
    DriverErrorCode.ECR_MODEL_NOT_SUPPORTED: "Данная модель ККТ не поддерживается",

    # Ошибки маркировки (401-426)
    DriverErrorCode.MARKING_CODE_VALIDATION_IN_PROGRESS: "Процедура проверки КМ уже запущена",
    DriverErrorCode.NO_CONNECTION_WITH_SERVER: "Ошибка соединения с сервером",
    DriverErrorCode.MARKING_CODE_VALIDATION_CANCELED: "Процедура проверки КМ прервана",
    DriverErrorCode.INVALID_MARKING_CODE_STATUS: "Некорректное значение статуса КМ",
    DriverErrorCode.INVALID_GS1: "Неверный код GS1",
    DriverErrorCode.MARKING_WORK_DENIED: "Запрещена работа с маркированным товарами",
    DriverErrorCode.MARKING_WORK_TEMPORARY_BLOCKED: "Работа с маркированными товарами временно заблокирована",
    DriverErrorCode.MARKS_OVERFLOW: "Переполнена таблица хранения КМ",
    DriverErrorCode.INVALID_MARKING_CODE: "Некорректный код маркировки",
    DriverErrorCode.INVALID_STATE: "Неверное состояние",
    DriverErrorCode.OFD_EXCHANGE: "Ошибка обмена с сервером ОФД или ИСМ",
    DriverErrorCode.INVALID_MEASUREMENT_UNIT: "Некорректное значение единиц измерения",
    DriverErrorCode.OPERATION_DENIED_IN_CURRENT_FFD: "Операция не разрешена в данной версии ФФД",
    DriverErrorCode.MARKING_OPERATION_DENIED: "Операция не разрешена",
    DriverErrorCode.NO_DATA_TO_SEND: "Нет данных для отправки",
    DriverErrorCode.NO_MARKED_POSITION: "Нет маркированных позиций в чеке",
    DriverErrorCode.HAS_NOT_SEND_NOTICES: "Имеются неотправленные уведомления",
    DriverErrorCode.UPDATE_KEYS_REQUIRED: "Требуется повторное обновление ключей",
    DriverErrorCode.UPDATE_KEYS_SERVICE: "Ошибка сервиса обновления ключей",
    DriverErrorCode.MARK_NOT_CHECKED: "КМ не проверен в ФН",
    DriverErrorCode.MARK_CHECK_TIMEOUT_EXPIRED: "Истёк таймаут проверки КМ",
    DriverErrorCode.NO_MARKING_CODE_IN_TABLE: "КМ отсутствует в таблице",
    DriverErrorCode.CHEKING_MARK_IN_PROGRESS: "Выполняется проверка КМ",
    DriverErrorCode.INVALID_SERVER_ADDRESS: "Настройки адреса сервера не заданы",
    DriverErrorCode.UPDATE_KEYS_TIMEOUT: "Истёк таймаут обновления ключей",
    DriverErrorCode.PROPERTY_FOR_MARKING_POSITION_ONLY: "Реквизит только для маркированной позиции",

    # Ошибки скриптов (501-504)
    DriverErrorCode.RECEIPT_PARSE_ERROR: "Ошибка парсинга запроса",
    DriverErrorCode.INTERRUPTED_BY_PREVIOUS_ERRORS: "Выполнение прервано из-за предыдущих ошибок",
    DriverErrorCode.DRIVER_SCRIPT_ERROR: "Ошибка скрипта драйвера",
    DriverErrorCode.VALIDATE_FUNC_NOT_FOUND: "Функция проверки задания не найдена",

    # Ошибки удалённого подключения (601-603)
    DriverErrorCode.RCP_SERVER_BUSY: "Устройство занято другим клиентом",
    DriverErrorCode.RCP_SERVER_VERSION: "Некорректная версия протокола",
    DriverErrorCode.RCP_SERVER_EXCHANGE: "Ошибка обмена с сервером",
})


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
