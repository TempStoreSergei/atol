import json
import uuid
import redis
from fastapi import HTTPException, status
from atol_integration.config.settings import settings
from atol_integration.utils.logger import logger

class RedisClient:
    def __init__(self, host=settings.redis_host, port=settings.redis_port):
        try:
            self.redis_conn = redis.Redis(host=host, port=port, decode_responses=True)
            self.redis_conn.ping() # Проверяем соединение при инициализации
            logger.info(f"Successfully connected to Redis at {host}:{port}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {host}:{port}: {e}")
            # В случае падения Redis при старте, приложение не должно падать.
            # Ошибки будут возникать при попытке выполнить команду.
            self.redis_conn = None

    def execute_command(self, command: str, kwargs: dict = None, timeout: int = 15):
        if not self.redis_conn:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection is not available."
            )

        command_id = str(uuid.uuid4())
        command_channel = "command_fr_channel"
        response_channel = f"{command_channel}_response"

        command_data = {
            "command_id": command_id,
            "command": command,
            "kwargs": kwargs or {}
        }

        pubsub = self.redis_conn.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(response_channel)

        try:
            self.redis_conn.publish(command_channel, json.dumps(command_data, ensure_ascii=False))
            logger.debug(f"Published command '{command}' ({command_id}) to Redis channel '{command_channel}'")

            while True:
                message = pubsub.get_message(timeout=timeout)
                if message is None: # Timeout
                    logger.error(f"Timeout waiting for response for command {command_id}")
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail="Timeout waiting for response from fiscal registrar worker."
                    )

                response_data = json.loads(message['data'])
                if response_data.get("command_id") == command_id:
                    logger.debug(f"Received response for command {command_id}: {response_data}")
                    
                    # Пробрасываем ошибку от воркера клиенту
                    if not response_data.get("success"):
                        detail = response_data.get("message", "Unknown error from worker")
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=detail
                        )
                    
                    # Возвращаем данные от воркера или стандартный успешный ответ
                    return response_data.get("data") or {"success": True, "message": response_data.get("message")}

        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis connection error during command execution: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to Redis during command execution."
            )
        finally:
            pubsub.unsubscribe(response_channel)
            pubsub.close()

# Глобальный экземпляр клиента для использования в приложении
redis_client = RedisClient()

def get_redis_client():
    """Зависимость FastAPI для получения клиента Redis."""
    return redis_client
