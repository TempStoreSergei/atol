"""
Модуль для запросов информации от ККТ через queryData()

Предоставляет единый интерфейс для всех типов запросов без дублирования кода.
"""
from typing import Dict, Any, Optional
from ..api.libfptr10 import IFptr
from ..api.driver import AtolDriver, AtolDriverError


class QueryDataService:
    """Сервис для выполнения запросов queryData к ККТ"""

    def __init__(self, driver: AtolDriver):
        """
        Инициализация сервиса

        Args:
            driver: Экземпляр драйвера АТОЛ
        """
        self.driver = driver
        self.fptr = driver.fptr

    def _execute_query(self, data_type: int, params: Optional[Dict[int, Any]] = None) -> int:
        """
        Выполнить запрос queryData с заданными параметрами

        Args:
            data_type: Тип запроса (LIBFPTR_DT_*)
            params: Дополнительные параметры для запроса

        Returns:
            int: Результат выполнения (0 - успех, -1 - ошибка)

        Raises:
            AtolDriverError: При ошибке выполнения запроса
        """
        # Устанавливаем тип запроса
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, data_type)

        # Устанавливаем дополнительные параметры
        if params:
            for param_id, param_value in params.items():
                self.fptr.setParam(param_id, param_value)

        # Выполняем запрос
        result = self.fptr.queryData()
        if result < 0:
            raise AtolDriverError(f"Ошибка запроса: {self.fptr.errorDescription()}")

        return result

    # ========== БАЗОВЫЕ ЗАПРОСЫ СТАТУСА ==========

    def get_status(self) -> Dict[str, Any]:
        """
        Запрос общей информации и статуса ККТ (LIBFPTR_DT_STATUS)

        Returns:
            dict: Полная информация о состоянии ККТ
        """
        self._execute_query(IFptr.LIBFPTR_DT_STATUS)

        return {
            "operator_id": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_OPERATOR_ID),
            "logical_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_LOGICAL_NUMBER),
            "shift_state": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
            "model": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL),
            "mode": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODE),
            "submode": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SUBMODE),
            "receipt_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER),
            "document_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            "shift_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            "receipt_type": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
            "document_type": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_TYPE),
            "line_length": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH),
            "line_length_pix": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX),
            "receipt_sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
            "is_fiscal_device": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FISCAL),
            "is_fiscal_fn": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_FISCAL),
            "is_fn_present": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_FN_PRESENT),
            "is_invalid_fn": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_INVALID_FN),
            "is_cashdrawer_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
            "is_paper_present": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
            "is_paper_near_end": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
            "is_cover_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
            "is_printer_connection_lost": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_CONNECTION_LOST),
            "is_printer_error": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_ERROR),
            "is_cut_error": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CUT_ERROR),
            "is_printer_overheat": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PRINTER_OVERHEAT),
            "is_device_blocked": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_BLOCKED),
            "date_time": self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat(),
            "serial_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),
            "model_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
            "firmware_version": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }

    def get_short_status(self) -> Dict[str, Any]:
        """Короткий запрос статуса ККТ (LIBFPTR_DT_SHORT_STATUS)"""
        self._execute_query(IFptr.LIBFPTR_DT_SHORT_STATUS)

        return {
            "is_cashdrawer_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
            "is_paper_present": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
            "is_paper_near_end": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
            "is_cover_opened": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED)
        }

    def get_cash_sum(self) -> Dict[str, float]:
        """Запрос суммы наличных в денежном ящике (LIBFPTR_DT_CASH_SUM)"""
        self._execute_query(IFptr.LIBFPTR_DT_CASH_SUM)
        return {"cash_sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}

    def get_unit_version(self, unit_type: int) -> Dict[str, str]:
        """Запрос версии модуля (LIBFPTR_DT_UNIT_VERSION)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_UNIT_VERSION,
            {IFptr.LIBFPTR_PARAM_UNIT_TYPE: unit_type}
        )

        response = {
            "unit_version": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }

        # Для конфигурации добавляем версию релиза
        if unit_type == 1:  # LIBFPTR_UT_CONFIGURATION
            response["release_version"] = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_RELEASE_VERSION)

        return response

    def get_shift_state(self) -> Dict[str, Any]:
        """Запрос состояния смены (LIBFPTR_DT_SHIFT_STATE)"""
        self._execute_query(IFptr.LIBFPTR_DT_SHIFT_STATE)

        return {
            "shift_state": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
            "shift_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            "date_time": self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()
        }

    def get_receipt_state(self) -> Dict[str, Any]:
        """Запрос состояния чека (LIBFPTR_DT_RECEIPT_STATE)"""
        self._execute_query(IFptr.LIBFPTR_DT_RECEIPT_STATE)

        return {
            "receipt_type": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
            "receipt_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_NUMBER),
            "document_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
            "receipt_sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
            "remainder": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_REMAINDER),
            "change": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_CHANGE)
        }

    def get_serial_number(self) -> Dict[str, str]:
        """Запрос заводского номера ККТ (LIBFPTR_DT_SERIAL_NUMBER)"""
        self._execute_query(IFptr.LIBFPTR_DT_SERIAL_NUMBER)
        return {"serial_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)}

    def get_model_info(self) -> Dict[str, Any]:
        """Запрос информации о модели ККТ (LIBFPTR_DT_MODEL_INFO)"""
        self._execute_query(IFptr.LIBFPTR_DT_MODEL_INFO)

        return {
            "model": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MODEL),
            "model_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
            "firmware_version": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        }

    def get_date_time(self) -> Dict[str, str]:
        """Запрос текущих даты и времени ККТ (LIBFPTR_DT_DATE_TIME)"""
        self._execute_query(IFptr.LIBFPTR_DT_DATE_TIME)
        return {"date_time": self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()}

    def get_receipt_line_length(self) -> Dict[str, int]:
        """Запрос ширины чековой ленты (LIBFPTR_DT_RECEIPT_LINE_LENGTH)"""
        self._execute_query(IFptr.LIBFPTR_DT_RECEIPT_LINE_LENGTH)

        return {
            "char_line_length": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH),
            "pix_line_length": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH_PIX)
        }

    # ========== СЧЕТЧИКИ И СУММЫ ==========

    def get_payment_sum(self, receipt_type: int, payment_type: int) -> Dict[str, float]:
        """Запрос суммы платежей за смену (LIBFPTR_DT_PAYMENT_SUM)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_PAYMENT_SUM,
            {
                IFptr.LIBFPTR_PARAM_RECEIPT_TYPE: receipt_type,
                IFptr.LIBFPTR_PARAM_PAYMENT_TYPE: payment_type
            }
        )
        return {"sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}

    def get_cashin_sum(self) -> Dict[str, float]:
        """Запрос суммы внесений (LIBFPTR_DT_CASHIN_SUM)"""
        self._execute_query(IFptr.LIBFPTR_DT_CASHIN_SUM)
        return {"sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}

    def get_cashout_sum(self) -> Dict[str, float]:
        """Запрос суммы выплат (LIBFPTR_DT_CASHOUT_SUM)"""
        self._execute_query(IFptr.LIBFPTR_DT_CASHOUT_SUM)
        return {"sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}

    def get_cashin_count(self) -> Dict[str, int]:
        """Запрос количества внесений (LIBFPTR_DT_CASHIN_COUNT)"""
        self._execute_query(IFptr.LIBFPTR_DT_CASHIN_COUNT)
        return {"count": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}

    def get_cashout_count(self) -> Dict[str, int]:
        """Запрос количества выплат (LIBFPTR_DT_CASHOUT_COUNT)"""
        self._execute_query(IFptr.LIBFPTR_DT_CASHOUT_COUNT)
        return {"count": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}

    def get_receipt_count(self, receipt_type: int) -> Dict[str, int]:
        """Запрос количества чеков (LIBFPTR_DT_RECEIPT_COUNT)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_RECEIPT_COUNT,
            {IFptr.LIBFPTR_PARAM_RECEIPT_TYPE: receipt_type}
        )
        return {"count": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)}

    # ========== СЕТЕВАЯ ИНФОРМАЦИЯ ==========

    def get_mac_address(self) -> Dict[str, str]:
        """Запрос MAC-адреса Ethernet (LIBFPTR_DT_MAC_ADDRESS)"""
        self._execute_query(IFptr.LIBFPTR_DT_MAC_ADDRESS)
        return {"mac_address": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MAC_ADDRESS)}

    def get_ethernet_info(self) -> Dict[str, Any]:
        """Запрос текущей конфигурации Ethernet (LIBFPTR_DT_ETHERNET_INFO)"""
        self._execute_query(IFptr.LIBFPTR_DT_ETHERNET_INFO)

        return {
            "ip": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_ETHERNET_IP),
            "mask": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_ETHERNET_MASK),
            "gateway": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_ETHERNET_GATEWAY),
            "dns": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_ETHERNET_DNS_IP),
            "timeout": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_ETHERNET_CONFIG_TIMEOUT),
            "port": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_ETHERNET_PORT),
            "dhcp": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_ETHERNET_DHCP),
            "dns_static": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_ETHERNET_DNS_STATIC)
        }

    def get_wifi_info(self) -> Dict[str, Any]:
        """Запрос текущей конфигурации Wi-Fi (LIBFPTR_DT_WIFI_INFO)"""
        self._execute_query(IFptr.LIBFPTR_DT_WIFI_INFO)

        return {
            "ip": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_WIFI_IP),
            "mask": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_WIFI_MASK),
            "gateway": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_WIFI_GATEWAY),
            "timeout": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_WIFI_CONFIG_TIMEOUT),
            "port": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_WIFI_PORT),
            "dhcp": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_WIFI_DHCP)
        }

    # ========== АППАРАТНАЯ ИНФОРМАЦИЯ ==========

    def get_printer_temperature(self) -> Dict[str, str]:
        """Запрос температуры ТПГ (LIBFPTR_DT_PRINTER_TEMPERATURE)"""
        self._execute_query(IFptr.LIBFPTR_DT_PRINTER_TEMPERATURE)
        return {"temperature": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_PRINTER_TEMPERATURE)}

    def get_power_source_state(self, power_source_type: int) -> Dict[str, Any]:
        """Запрос состояния источника питания (LIBFPTR_DT_POWER_SOURCE_STATE)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_POWER_SOURCE_STATE,
            {IFptr.LIBFPTR_PARAM_POWER_SOURCE_TYPE: power_source_type}
        )

        return {
            "battery_charge": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_BATTERY_CHARGE),
            "voltage": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_VOLTAGE),
            "use_battery": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_USE_BATTERY),
            "is_charging": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_BATTERY_CHARGING),
            "can_print_on_battery": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_CAN_PRINT_WHILE_ON_BATTERY)
        }

    def get_mcu_info(self) -> Dict[str, Any]:
        """Запрос информации о микроконтроллере (LIBFPTR_DT_MCU_INFO)"""
        self._execute_query(IFptr.LIBFPTR_DT_MCU_INFO)

        return {
            "mcu_sn": self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_MCU_SN),
            "mcu_part_id": self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_MCU_PART_ID),
            "mcu_part_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MCU_PART_NAME)
        }

    # ========== СПЕЦИФИЧНЫЕ ЗАПРОСЫ ==========

    def get_lk_user_code(self) -> Dict[str, str]:
        """Запрос кода привязки к ЛК (LIBFPTR_DT_LK_USER_CODE)"""
        self._execute_query(IFptr.LIBFPTR_DT_LK_USER_CODE)
        return {"lk_user_code": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_LK_USER_CODE)}

    def get_last_sent_ofd_document_datetime(self) -> Dict[str, str]:
        """Запрос даты последней отправки в ОФД (LIBFPTR_DT_LAST_SENT_OFD_DOCUMENT_DATE_TIME)"""
        self._execute_query(IFptr.LIBFPTR_DT_LAST_SENT_OFD_DOCUMENT_DATE_TIME)
        return {"date_time": self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()}

    def get_last_sent_ism_notice_datetime(self) -> Dict[str, str]:
        """Запрос даты последней отправки в ИСМ (LIBFPTR_DT_LAST_SENT_ISM_NOTICE_DATE_TIME)"""
        self._execute_query(IFptr.LIBFPTR_DT_LAST_SENT_ISM_NOTICE_DATE_TIME)
        return {"date_time": self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()}

    def get_scripts_info(self) -> Dict[str, Any]:
        """Запрос информации о загруженном шаблоне (LIBFPTR_DT_SCRIPTS_INFO)"""
        self._execute_query(IFptr.LIBFPTR_DT_SCRIPTS_INFO)

        return {
            "script_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SCRIPT_NAME),
            "script_hash": self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_SCRIPT_HASH)
        }

    def get_shift_totals(self, receipt_type: int) -> Dict[str, float]:
        """Запрос сменного итога (LIBFPTR_DT_SHIFT_TOTALS)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_SHIFT_TOTALS,
            {IFptr.LIBFPTR_PARAM_RECEIPT_TYPE: receipt_type}
        )
        return {"sum": self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}

    def get_font_info(self, font_number: int) -> Dict[str, int]:
        """Запрос параметров шрифта (LIBFPTR_DT_FONT_INFO)"""
        self._execute_query(
            IFptr.LIBFPTR_DT_FONT_INFO,
            {IFptr.LIBFPTR_PARAM_FONT: font_number}
        )

        return {
            "line_length": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_LINE_LENGTH),
            "font_width": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FONT_WIDTH)
        }

    def get_softlock_status(self) -> Dict[str, Any]:
        """Запрос состояния привязки к ПО (LIBFPTR_DT_SOFTLOCK_STATUS)"""
        self._execute_query(IFptr.LIBFPTR_DT_SOFTLOCK_STATUS)

        bounded = self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_BOUND)
        result = {"bounded": bounded}

        if bounded:
            result.update({
                "locked": self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_LOCKED),
                "days_count": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_COUNT),
                "soft_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SOFT_NAME)
            })

        return result

    def get_cache_requisites(self) -> Dict[str, Any]:
        """Запрос кэшированных реквизитов (LIBFPTR_DT_CACHE_REQUISITES)"""
        self._execute_query(IFptr.LIBFPTR_DT_CACHE_REQUISITES)

        return {
            "fn_serial_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FN_SERIAL_NUMBER),
            "ecr_registration_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_ECR_REGISTRATION_NUMBER),
            "ofd_vatin": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_OFD_VATIN),
            "fns_url": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FNS_URL),
            "ffd_version": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FFD_VERSION),
            "machine_number": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MACHINE_NUMBER)
        }
