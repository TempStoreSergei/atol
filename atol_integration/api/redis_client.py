import json
import uuid
import redis
import time
from fastapi import HTTPException, status
from ..config.settings import settings
from ..utils.logger import logger


class RedisClient:
    """Redis клиент для работы с несколькими фискальными регистраторами"""
    _instance = None

    def __new__(cls):
        """Реализация паттерна Singleton - создается только один экземпляр"""
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация клиента (выполняется только один раз)"""
        if self._initialized:
            return

        self.redis_conn = None

        try:
            self.redis_conn = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True
            )
            self.redis_conn.ping()
            logger.info(f"Successfully connected to Redis at {settings.redis_host}:{settings.redis_port}")
            self._initialized = True
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {settings.redis_host}:{settings.redis_port}: {e}")

    def execute_command(self, command: str, device_id: str = "default", kwargs: dict = None, timeout: int = 10):
        """
        Выполнить команду для конкретного фискального регистратора

        Args:
            command: Название команды
            device_id: Идентификатор устройства (по умолчанию "default")
            kwargs: Параметры команды
            timeout: Таймаут ожидания ответа в секундах
        """
        if not self.redis_conn:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection is not available."
            )

        # Формируем каналы для конкретного устройства
        command_channel = f"command_fr_{device_id}"
        response_channel = f"command_fr_{device_id}_response"

        # Подписываемся на канал ответов
        pubsub = self.redis_conn.pubsub()
        pubsub.subscribe(response_channel)

        # Генерируем ID команды
        command_id = str(uuid.uuid4())
        command_data = {
            "command_id": command_id,
            "command": command,
            "device_id": device_id,
            "kwargs": kwargs or {}
        }

        # Публикуем команду
        try:
            self.redis_conn.publish(command_channel, json.dumps(command_data, ensure_ascii=False))
            logger.info(f"Published command '{command}' ({command_id}) to device '{device_id}' on channel '{command_channel}'")
        except redis.exceptions.ConnectionError as e:
            pubsub.close()
            logger.error(f"Redis connection error during PUBLISH: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis PUBLISH failed.")

        # Ждём ответ
        start_time = time.time()
        try:
            for message in pubsub.listen():
                # Проверяем таймаут
                if time.time() - start_time > timeout:
                    logger.error(f"Timeout waiting for response for command {command_id} from device '{device_id}'")
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail=f"Timeout waiting for response from fiscal registrar '{device_id}' for command '{command}'."
                    )

                # Обрабатываем только сообщения
                if message['type'] == 'message':
                    try:
                        response_data = json.loads(message['data'])

                        # Проверяем, что это ответ на нашу команду
                        if response_data.get("command_id") == command_id:
                            logger.debug(f"Received response for command {command_id} from device '{device_id}': {response_data}")

                            if not response_data.get("success"):
                                detail = response_data.get("message", "Unknown error from worker")
                                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

                            return response_data.get("data") or {"success": True, "message": response_data.get("message")}

                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Could not parse response from Redis: {message.get('data')}, error: {e}")
                        continue

        finally:
            pubsub.close()


def get_redis_client() -> RedisClient:
    """
    Зависимость FastAPI для получения клиента Redis.

    Возвращает Singleton экземпляр RedisClient.
    """
    return RedisClient()
