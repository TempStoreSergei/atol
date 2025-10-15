import json
import uuid
import redis
import time
import threading
from fastapi import HTTPException, status
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger

class RedisClient:
    def __init__(self, host=settings.redis_host, port=settings.redis_port):
        self.redis_conn = None
        self.pubsub = None
        self.listener_thread = None
        self.responses = {}
        self.response_lock = threading.Lock()
        self.command_channel = "command_fr_channel"
        self.response_channel = f"{self.command_channel}_response"

        try:
            self.redis_conn = redis.Redis(host=host, port=port, decode_responses=True)
            self.redis_conn.ping()
            logger.info(f"Successfully connected to Redis at {host}:{port}")
            self._start_listener()
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {host}:{port}: {e}")

    def _start_listener(self):
        """Запускает фоновый поток для прослушивания ответов."""
        self.pubsub = self.redis_conn.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(self.response_channel)
        self.listener_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        self.listener_thread.start()
        logger.info(f"Redis listener started on channel '{self.response_channel}'")

    def _listen_for_responses(self):
        """Цикл, который слушает канал ответов и сохраняет их."""
        for message in self.pubsub.listen():
            try:
                response_data = json.loads(message['data'])
                command_id = response_data.get("command_id")
                if command_id:
                    with self.response_lock:
                        self.responses[command_id] = response_data
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Could not parse response from Redis: {message.get('data')}, error: {e}")

    def execute_command(self, command: str, kwargs: dict = None, timeout: int = 10):
        if not self.redis_conn or not self.listener_thread or not self.listener_thread.is_alive():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection or listener thread is not available."
            )

        command_id = str(uuid.uuid4())
        command_data = {
            "command_id": command_id,
            "command": command,
            "kwargs": kwargs or {}
        }

        try:
            self.redis_conn.publish(self.command_channel, json.dumps(command_data, ensure_ascii=False))
            logger.debug(f"Published command '{command}' ({command_id}) to '{self.command_channel}'")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error during PUBLISH: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis PUBLISH failed.")

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.response_lock:
                if command_id in self.responses:
                    response_data = self.responses.pop(command_id)
                    logger.debug(f"Received response for command {command_id}: {response_data}")
                    
                    if not response_data.get("success"):
                        detail = response_data.get("message", "Unknown error from worker")
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
                    
                    return response_data.get("data") or {"success": True, "message": response_data.get("message")}
            
            time.sleep(0.01)  # Небольшая пауза, чтобы не загружать CPU

        logger.error(f"Timeout waiting for response for command {command_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout waiting for response from fiscal registrar worker for command '{command}'."
        )

# Глобальный экземпляр клиента для использования в приложении
redis_client = RedisClient()

def get_redis_client():
    """Зависимость FastAPI для получения клиента Redis."""
    return redis_client