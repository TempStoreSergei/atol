import json
import datetime
from typing import Any, Dict
import redis
from atol_integration.api.driver import AtolDriver, AtolDriverError
from atol_integration.api.libfptr10 import IFptr
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger

# Глобальный экземпляр драйвера
driver = AtolDriver()
fptr = driver.fptr

def _check_result(result: int, operation: str):
    """Проверяет результат выполнения операции драйвера"""
    if result < 0:
        # Используем errorDescription() для получения текста ошибки
        error_description = fptr.errorDescription()
        error_code = fptr.errorCode()
        raise AtolDriverError(f"Ошибка {operation}: {error_description}", error_code=error_code)

def process_command(command_data: Dict[str, Any]) -> Dict[str, Any]:
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
                fptr.setSettings(json.dumps(kwargs['settings']))
            _check_result(fptr.open(), "открытия соединения")
            response['success'] = True
            response['message'] = "Соединение с ККТ успешно установлено"

        elif command == 'connection_close':
            _check_result(fptr.close(), "закрытия соединения")
            response['success'] = True
            response['message'] = "Соединение с ККТ закрыто"

        elif command == 'connection_is_opened':
            is_opened = fptr.isOpened()
            response['success'] = True
            response['data'] = {'is_opened': is_opened}
            response['message'] = "Соединение активно" if is_opened else "Соединение не установлено"

        # ======================================================================
        # Shift Commands
        # ======================================================================
        elif command == 'shift_open':
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            _check_result(fptr.openShift(), "открытия смены")
            shift_number = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            response['success'] = True
            response['message'] = f"Смена #{shift_number} успешно открыта"
            response['data'] = {'shift_number': shift_number}

        elif command == 'shift_close':
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            _check_result(fptr.closeShift(), "закрытия смены")
            response['success'] = True
            response['data'] = {
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                "fiscal_document_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
            }
            response['message'] = "Смена успешно закрыта, Z-отчет напечатан"

        # ======================================================================
        # Receipt Commands
        # ======================================================================
        elif command == 'receipt_open':
            fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, kwargs['receipt_type'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            if kwargs.get('customer_contact'):
                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
                fptr.setParam(IFptr.LIBFPTR_PARAM_BUYER_EMAIL_OR_PHONE, kwargs['customer_contact'])
            _check_result(fptr.openReceipt(), "открытия чека")
            response['success'] = True
            response['message'] = f"Чек типа {kwargs['receipt_type']} успешно открыт"

        elif command == 'receipt_add_item':
            for key, value in kwargs.items():
                if key == 'name': fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, value)
                elif key == 'price': fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, value)
                elif key == 'quantity': fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, value)
                elif key == 'tax_type': fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, value)
                elif key == 'payment_method': fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE_SIGN, value)
                elif key == 'payment_object': fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_SIGN, value)
            _check_result(fptr.registration(), "регистрации позиции")
            response['success'] = True
            response['message'] = f"Позиция '{kwargs['name']}' добавлена"

        elif command == 'receipt_add_payment':
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, kwargs['payment_type'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, kwargs['amount'])
            _check_result(fptr.payment(), "регистрации оплаты")
            response['success'] = True
            response['message'] = f"Оплата {kwargs['amount']:.2f} добавлена"

        elif command == 'receipt_close':
            _check_result(fptr.closeReceipt(), "закрытия чека")
            response['success'] = True
            response['data'] = {
                "fiscal_document_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
                "fiscal_document_sign": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            }
            response['message'] = "Чек успешно закрыт и напечатан"

        # ======================================================================
        # Query Commands (All of them)
        # ======================================================================
        elif command == 'get_status':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
            _check_result(fptr.queryData(), "запроса статуса")
            response['data'] = {
                "model_name": fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME),
                "serial_number": fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER),
                "shift_state": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
                "cover_opened": fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
                "paper_present": fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
            }
            response['success'] = True

        elif command == 'get_short_status':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHORT_STATUS)
            _check_result(fptr.queryData(), "короткого запроса статуса")
            response['data'] = {
                "cashdrawer_opened": fptr.getParamBool(IFptr.LIBFPTR_PARAM_CASHDRAWER_OPENED),
                "paper_present": fptr.getParamBool(IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT),
                "paper_near_end": fptr.getParamBool(IFptr.LIBFPTR_PARAM_PAPER_NEAR_END),
                "cover_opened": fptr.getParamBool(IFptr.LIBFPTR_PARAM_COVER_OPENED),
            }
            response['success'] = True

        elif command == 'get_cash_sum':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASH_SUM)
            _check_result(fptr.queryData(), "запроса суммы наличных")
            response['data'] = {"cash_sum": fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)}
            response['success'] = True

        elif command == 'get_shift_state':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
            _check_result(fptr.queryData(), "запроса состояния смены")
            dt = fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
            response['data'] = {
                "shift_state": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE),
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                "date_time": dt.isoformat() if isinstance(dt, datetime.datetime) else None,
            }
            response['success'] = True
        
        elif command == 'get_receipt_state':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_RECEIPT_STATE)
            _check_result(fptr.queryData(), "запроса состояния чека")
            response['data'] = {
                "receipt_type": fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE),
                "receipt_sum": fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM),
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
    logger.info(f"Ожидание команд в канале '{channel}'...")

    for message in pubsub.listen():
        if message.get('type') == 'message':
            if message.get('data') == 'ping':
                continue
            try:
                command_data = json.loads(message.get('data'))
                logger.debug(f"Получена команда: {command_data}")
                response = process_command(command_data)
                r.publish(response_channel, json.dumps(response, ensure_ascii=False))
                logger.debug(f"Ответ отправлен в канал '{response_channel}': {response}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга команды: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    listen_to_redis()