"""
FastAPI REST API сервер для АТОЛ ККТ

Перенаправляет все запросы на выполнение в Redis очередь.
"""
import logging
from fastapi import FastAPI, HTTPException, status

# Импорты роутеров
from ..routes import (
    cash_routes,
    connection_routes,
    print_routes,
    query_routes,
    receipt_routes,
    shift_routes,
)
from .redis_client import redis_client

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
app.include_router(connection_routes.router)
app.include_router(receipt_routes.router)
app.include_router(shift_routes.router)
app.include_router(cash_routes.router)
app.include_router(print_routes.router)
app.include_router(query_routes.router)

logger.info("✓ Все роутеры подключены к приложению")


# ========== БАЗОВЫЕ ENDPOINTS ==========

@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint с информацией о API"""
    redis_ok = False
    try:
        if redis_client.redis_conn:
            redis_ok = redis_client.redis_conn.ping()
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
        if redis_client.redis_conn:
            redis_ok = redis_client.redis_conn.ping()
    except Exception:
        redis_ok = False

    if not redis_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection failed.",
        )
    return {"status": "healthy", "redis_connected": True}