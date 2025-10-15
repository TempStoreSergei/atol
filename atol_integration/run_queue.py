import json
import redis
from atol_integration.api.driver import AtolDriver
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger

# Глобальный экземпляр драйвера
driver = AtolDriver()

def process_command(command_data):
    """Выполнение команды на основе полученной из pubsub"""
    response = {
        "command_id": command_data.get('command_id'),
        "success": False,
        "message": None,
        "data": None,
    }

    try:
        command = command_data.get('command')
        kwargs = command_data.get('kwargs', {})

        if command == 'connect':
            # Пример: {'host': '192.168.1.100', 'port': 5555}
            result = driver.connect(**kwargs)
            response['success'] = result
            response['message'] = "Соединение установлено" if result else "Ошибка соединения"
        
        elif command == 'disconnect':
            driver.disconnect()
            response['success'] = True
            response['message'] = "Соединение закрыто"

        elif command == 'open_shift':
            # Пример: {'cashier_name': 'Иванов И.И.'}
            data = driver.open_shift(**kwargs)
            response['success'] = True
            response['data'] = data

        elif command == 'close_shift':
            # Пример: {'cashier_name': 'Иванов И.И.'}
            data = driver.close_shift(**kwargs)
            response['success'] = True
            response['data'] = data
        
        elif command == 'x_report':
            result = driver.x_report()
            response['success'] = result
            response['message'] = "X-отчет напечатан" if result else "Ошибка печати X-отчета"

        else:
            response['message'] = f"Неизвестная команда: {command}"

    except Exception as e:
        error_msg = f"Ошибка при выполнении команды '{command_data.get('command')}': {str(e)}"
        logger.error(error_msg)
        response["message"] = error_msg
        if hasattr(e, 'to_dict'):
            response['data'] = e.to_dict()

    return response


# Эту функцию не менять!
def listen_to_redis():
    """Подключение к Redis и обработка команд"""
    # Подключение к Redis
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    pubsub = r.pubsub()

    channel = 'command_fr_channel'
    response_channel = f'{channel}_response'
    pubsub.subscribe(channel)
    logger.info(f"Ожидание команд в канале '{channel}'...")

    # Слушаем канал и выполняем команды
    for message in pubsub.listen():
        if message.get('type') == 'message':
            # обработка пинга при проверке доступности канала
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