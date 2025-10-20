"""
FastAPI REST API сервер для АТОЛ ККТ

Перенаправляет все запросы на выполнение в Redis очередь.
"""
import logging
from fastapi import FastAPI, HTTPException, status

from ..routes import (
    cash_routes,
    config_routes,
    connection_routes,
    operator_routes,
    print_routes,
    query_routes,
    receipt_routes,
    shift_routes,
)
from redis.asyncio import Redis
from .dependencies import get_redis
from ..config.settings import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Создание FastAPI приложения
app = FastAPI(
    title="АТОЛ ККТ API (через Redis)",
    description="REST API для асинхронной работы с кассовым оборудованием АТОЛ через Redis.",
    version="0.4.0",
)


# ========== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ==========

# Список всех роутеров приложения
routers = []
routers.append(receipt_routes.router())
routers.append(shift_routes.router())
routers.append(cash_routes.router())
routers.append(connection_routes.router())
routers.append(operator_routes.router())
routers.append(query_routes.router())
routers.append(print_routes.router())
routers.append(config_routes.router())

# Подключаем все роутеры к приложению
for router in routers:
    app.include_router(router)

logger.info(f"✓ Подключено {len(routers)} роутеров к приложению")


# ========== БАЗОВЫЕ ENDPOINTS ==========

@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint с информацией о API"""
    redis_ok = False
    try:
        redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        redis_ok = await redis.ping()
        await redis.close()
    except Exception:
        redis_ok = False

    return {
        "name": "АТОЛ ККТ API (через Redis)",
        "version": "0.4.0",
        "status": "running",
        "redis_connected": redis_ok,
    }


@app.get("/health", tags=["System"])
async def health():
    """Проверка здоровья сервиса"""
    redis_ok = False
    try:
        redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        redis_ok = await redis.ping()
        await redis.close()
    except Exception:
        redis_ok = False

    if not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection failed.",
        )
    return {"status": "healthy", "redis_connected": True}
