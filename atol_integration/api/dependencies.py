"""
Зависимости FastAPI и утилиты для работы с Redis
"""
import json
import asyncio
from uuid import uuid4
from redis.asyncio import Redis
from fastapi import HTTPException

from ..config.settings import settings
from ..utils.logger import logger


async def get_redis():
    """
    Получение объекта Redis как зависимость FastAPI.

    Yields:
        Redis: Асинхронное подключение к Redis

    Raises:
        HTTPException: Если Redis недоступен
    """
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )
    try:
        await redis.ping()
        logger.debug(f"Successfully connected to Redis at {settings.redis_host}:{settings.redis_port}")
        yield redis
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(500, f'Redis не доступен: {e}')
    finally:
        await redis.close()


async def wait_for_response(pubsub, command_id: str, timeout: int = 10):
    """
    Ожидание ответа из Redis Pub/Sub с проверкой command_id.

    Args:
        pubsub: Redis PubSub объект
        command_id: ID команды для проверки
        timeout: Таймаут ожидания в секундах

    Returns:
        dict: Данные ответа

    Raises:
        asyncio.TimeoutError: Если истек timeout
        ValueError: Если получен некорректный JSON
        HTTPException: Если команда вернула ошибку
    """
    async def _listener():
        async for message in pubsub.listen():
            if message.get("type") == "message":
                try:
                    data = json.loads(message["data"])
                    if data.get('command_id') == command_id:
                        logger.debug(f"Received response for command {command_id}: {data}")

                        # Проверяем успешность выполнения команды
                        if not data.get("success"):
                            detail = data.get("message", "Unknown error from worker")
                            raise HTTPException(status_code=400, detail=detail)

                        return data
                except json.JSONDecodeError as e:
                    logger.error(f"Некорректный JSON в сообщении: {message}")
                    raise ValueError(f"Некорректный JSON в сообщении: {message}")

    try:
        return await asyncio.wait_for(_listener(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Timeout waiting for response for command {command_id}")
        raise HTTPException(
            status_code=504,
            detail=f"Timeout waiting for response from fiscal registrar for command"
        )


async def pubsub_command_util(
    redis: Redis,
    device_id: str = "default",
    command: str = "",
    kwargs: dict = None,
    timeout: int = 10
):
    """
    Функция создает подписчика и слушателя Redis для выполнения команды.

    Args:
        redis: Асинхронный Redis клиент
        device_id: Идентификатор устройства (по умолчанию "default")
        command: Название команды для выполнения
        kwargs: Параметры команды
        timeout: Таймаут ожидания ответа в секундах

    Returns:
        dict: Результат выполнения команды

    Raises:
        HTTPException: При ошибках выполнения команды или timeout
    """
    # Формируем каналы для конкретного устройства
    command_channel = f"command_fr_{device_id}"
    response_channel = f"command_fr_{device_id}_response"

    # Генерируем уникальный ID команды
    command_id = str(uuid4())

    # Формируем данные команды
    command_data = {
        "command_id": command_id,
        "command": command,
        "device_id": device_id,
        "kwargs": kwargs or {}
    }

    # Создаём подписчика на канал ответов
    pubsub = redis.pubsub()
    await pubsub.subscribe(response_channel)

    try:
        # Отправляем команду
        await redis.publish(command_channel, json.dumps(command_data, ensure_ascii=False))
        logger.info(f"Published command '{command}' ({command_id}) to device '{device_id}' on channel '{command_channel}'")

        # Ждём ответ
        response_data = await wait_for_response(pubsub, command_id, timeout=timeout)

        # Возвращаем данные ответа или success message
        return response_data.get("data") or {"success": True, "message": response_data.get("message")}

    finally:
        # Отписываемся от канала
        await pubsub.unsubscribe(response_channel)
        await pubsub.close()
