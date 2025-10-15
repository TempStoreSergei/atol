import json
from typing import Any, Dict
import redis
from atol_integration.api.driver import AtolDriver, AtolDriverError
from atol_integration.api.libfptr10 import IFptr
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger

# Глобальный экземпляр драйвера
driver = AtolDriver()
fptr = driver.fptr

def _check_result(operation: str):
    if fptr.result() < 0:
        raise AtolDriverError(f"Ошибка {operation}: {fptr.errorDescription()}", error_code=fptr.errorCode())

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
            if 'settings' in kwargs:
                fptr.setSettings(kwargs['settings'])
            fptr.open()
            _check_result("открытия соединения")
            response['success'] = True
            response['message'] = "Соединение с ККТ успешно установлено"

        elif command == 'connection_close':
            fptr.close()
            _check_result("закрытия соединения")
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
            fptr.openShift()
            _check_result("открытия смены")
            shift_number = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
            response['success'] = True
            response['message'] = f"Смена #{shift_number} успешно открыта"
            response['data'] = {'shift_number': shift_number}

        elif command == 'shift_close':
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            fptr.closeShift()
            _check_result("закрытия смены")
            response['success'] = True
            response['data'] = {
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                "fiscal_document_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
                "fiscal_document_sign": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
                "fiscal_storage_number": fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_STORAGE_NUMBER),
            }
            response['message'] = "Смена успешно закрыта, Z-отчет напечатан"

        elif command == 'shift_get_status':
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
            fptr.queryData()
            _check_result("запроса статуса смены")
            shift_state = fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
            shift_opened = (shift_state in [1, 3])
            response['success'] = True
            response['data'] = {
                "shift_opened": shift_opened,
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                "shift_expired": (shift_state == 3),
                "receipts_count": fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER) if shift_opened else None
            }

        elif command == 'shift_print_x_report':
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)
            fptr.report()
            _check_result("печати X-отчета")
            response['success'] = True
            response['message'] = "X-отчет успешно напечатан"

        # ======================================================================
        # Receipt Commands
        # ======================================================================
        elif command == 'receipt_open':
            fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, kwargs['receipt_type'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            if kwargs.get('customer_contact'):
                fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)
                fptr.setParam(IFptr.LIBFPTR_PARAM_BUYER_EMAIL_OR_PHONE, kwargs['customer_contact'])
            fptr.openReceipt()
            _check_result("открытия чека")
            response['success'] = True
            response['message'] = f"Чек типа {kwargs['receipt_type']} успешно открыт"

        elif command == 'receipt_add_item':
            fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, kwargs['name'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, kwargs['price'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, kwargs['quantity'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, kwargs['tax_type'])
            if 'payment_method' in kwargs:
                fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE_SIGN, kwargs['payment_method'])
            if 'payment_object' in kwargs:
                fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_SIGN, kwargs['payment_object'])
            fptr.registration()
            _check_result("регистрации позиции")
            response['success'] = True
            response['message'] = f"Позиция '{kwargs['name']}' добавлена"

        elif command == 'receipt_add_payment':
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, kwargs['payment_type'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, kwargs['amount'])
            fptr.payment()
            _check_result("регистрации оплаты")
            response['success'] = True
            response['message'] = f"Оплата {kwargs['amount']:.2f} добавлена"

        elif command == 'receipt_close':
            fptr.closeReceipt()
            _check_result("закрытия чека")
            response['success'] = True
            response['data'] = {
                "fiscal_document_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
                "fiscal_document_sign": fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
                "fiscal_storage_number": fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_STORAGE_NUMBER),
                "shift_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
                "receipt_number": fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER),
                "fiscal_document_datetime": fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).isoformat()
            }
            response['message'] = "Чек успешно закрыт и напечатан"

        elif command == 'receipt_cancel':
            fptr.cancelReceipt()
            _check_result("отмены чека")
            response['success'] = True
            response['message'] = "Чек успешно отменён"

        # ======================================================================
        # Cash Commands
        # ======================================================================
        elif command == 'cash_in':
            fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, kwargs['amount'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            fptr.cashIncome()
            _check_result("внесения наличных")
            response['success'] = True
            response['message'] = f"Внесение {kwargs['amount']:.2f} руб. успешно выполнено"

        elif command == 'cash_out':
            fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, kwargs['amount'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, kwargs['cashier_name'])
            fptr.cashOutcome()
            _check_result("изъятия наличных")
            response['success'] = True
            response['message'] = f"Изъятие {kwargs['amount']:.2f} руб. успешно выполнено"
        
        elif command == 'cash_drawer_open':
            fptr.openCashDrawer()
            _check_result("открытия денежного ящика")
            response['success'] = True
            response['message'] = "Команда на открытие денежного ящика отправлена"

        # ======================================================================
        # Print Commands
        # ======================================================================
        elif command == 'print_text':
            fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, kwargs['text'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_LEFT))
            fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT_WRAP, kwargs.get('wrap', IFptr.LIBFPTR_TW_AUTO))
            fptr.printText()
            _check_result("печати текста")
            response['success'] = True
            response['message'] = "Текст напечатан"

        elif command == 'print_barcode':
            fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, kwargs['barcode'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, kwargs['barcode_type'])
            fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, kwargs.get('alignment', IFptr.LIBFPTR_ALIGNMENT_CENTER))
            fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, kwargs.get('scale', 2))
            fptr.printBarcode()
            _check_result("печати штрихкода")
            response['success'] = True
            response['message'] = "Штрихкод напечатан"

        # ======================================================================
        # Query Commands (Generic)
        # ======================================================================
        elif command == 'query_data':
            # Generic command to access all queryData functions
            # kwargs: {'data_type': int, 'params': {param_id: value, ...}}
            fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, kwargs['data_type'])
            if 'params' in kwargs:
                for p_id, p_val in kwargs['params'].items():
                    fptr.setParam(p_id, p_val)
            fptr.queryData()
            _check_result(f"запроса данных (тип {kwargs['data_type']})")
            
            # The client is responsible for knowing what params to get
            response['success'] = True
            response['message'] = "Запрос данных выполнен"
            # Example of how a client could get the result:
            # response['data'] = {'serial': fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)}

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
                logger.info(f"Получена команда: {command_data}")

                response = process_command(command_data)

                r.publish(response_channel, json.dumps(response, ensure_ascii=False))
                logger.info(f"Ответ отправлен в канал '{response_channel}': {response}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга команды: {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    listen_to_redis()
