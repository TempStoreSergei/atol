import json
import uuid
import redis
import time
import threading
from fastapi import HTTPException, status
from ..config.settings import settings
from ..utils.logger import logger


class RedisClient:
    """Redis клиент для работы с несколькими фискальными регистраторами"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Реализация паттерна Singleton - создается только один экземпляр"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RedisClient, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация клиента (выполняется только один раз)"""
        if self._initialized:
            return

        self.redis_conn = None
        self.pubsub = None
        self.listener_thread = None
        self.responses = {}
        self.response_lock = threading.Lock()

        # Паттерн каналов для устройств
        self.device_channels = {}  # {device_id: {"command": channel, "response": response_channel}}

        try:
            self.redis_conn = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True
            )
            self.redis_conn.ping()
            logger.info(f"Successfully connected to Redis at {settings.redis_host}:{settings.redis_port}")
            self._start_listener()
            self._initialized = True
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {settings.redis_host}:{settings.redis_port}: {e}")

    def _get_device_channels(self, device_id: str) -> dict:
        """Получить каналы для конкретного устройства"""
        if device_id not in self.device_channels:
            self.device_channels[device_id] = {
                "command": f"command_fr_{device_id}",
                "response": f"command_fr_{device_id}_response"
            }
            # Подписываемся на канал ответов для нового устройства
            with self._lock:
                self.pubsub.subscribe(self.device_channels[device_id]["response"])
                time.sleep(0.01)  # Небольшая пауза для обработки подписки
            logger.info(f"Subscribed to response channel for device '{device_id}': {self.device_channels[device_id]['response']}")
        return self.device_channels[device_id]

    def _start_listener(self):
        """Запускает фоновый поток для прослушивания ответов от всех устройств."""
        self.pubsub = self.redis_conn.pubsub(ignore_subscribe_messages=True)
        self.listener_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        self.listener_thread.start()

        # Даём потоку время запуститься
        time.sleep(0.1)

        if self.listener_thread.is_alive():
            logger.info(f"Redis listener started for multiple devices")
        else:
            logger.error("Redis listener failed to start!")
            raise Exception("Failed to start Redis listener thread")

    def _listen_for_responses(self):
        """Цикл, который слушает канал ответов и сохраняет их."""
        try:
            logger.info("Listener thread started, waiting for messages...")
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        response_data = json.loads(message['data'])
                        command_id = response_data.get("command_id")
                        if command_id:
                            with self.response_lock:
                                self.responses[command_id] = response_data
                            logger.debug(f"Response received for command_id={command_id}")
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Could not parse response from Redis: {message.get('data')}, error: {e}")
        except Exception as e:
            logger.error(f"Listener thread crashed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def execute_command(self, command: str, device_id: str = "default", kwargs: dict = None, timeout: int = 10):
        """
        Выполнить команду для конкретного фискального регистратора

        Args:
            command: Название команды
            device_id: Идентификатор устройства (по умолчанию "default")
            kwargs: Параметры команды
            timeout: Таймаут ожидания ответа в секундах
        """
        # Детальная проверка состояния
        if not self.redis_conn:
            logger.error("Redis connection is not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection is not initialized."
            )

        if not self.listener_thread:
            logger.error("Listener thread is not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis listener thread is not initialized."
            )

        if not self.listener_thread.is_alive():
            logger.error("Listener thread is not alive")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis listener thread is not running."
            )

        # Получаем каналы для конкретного устройства
        channels = self._get_device_channels(device_id)
        command_channel = channels["command"]

        command_id = str(uuid.uuid4())
        command_data = {
            "command_id": command_id,
            "command": command,
            "device_id": device_id,
            "kwargs": kwargs or {}
        }

        try:
            self.redis_conn.publish(command_channel, json.dumps(command_data, ensure_ascii=False))
            logger.info(f"Published command '{command}' ({command_id}) to device '{device_id}' on channel '{command_channel}'")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error during PUBLISH: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis PUBLISH failed.")

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.response_lock:
                if command_id in self.responses:
                    response_data = self.responses.pop(command_id)
                    logger.debug(f"Received response for command {command_id} from device '{device_id}': {response_data}")

                    if not response_data.get("success"):
                        detail = response_data.get("message", "Unknown error from worker")
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

                    return response_data.get("data") or {"success": True, "message": response_data.get("message")}

            time.sleep(0.01)  # Небольшая пауза, чтобы не загружать CPU

        logger.error(f"Timeout waiting for response for command {command_id} from device '{device_id}'")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout waiting for response from fiscal registrar '{device_id}' for command '{command}'."
        )

def get_redis_client() -> RedisClient:
    """
    Зависимость FastAPI для получения клиента Redis.

    Возвращает Singleton экземпляр RedisClient.
    Не использует глобальные переменные!
    """
    return RedisClient()