"""
Главное FastAPI приложение для работы с драйвером АТОЛ ККТ v.10
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import router
from .driver import AtolDriverError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="ATOL Driver API",
    description="REST API для работы с драйвером АТОЛ ККТ v.10 (libfptr10)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутера
app.include_router(router)


# Обработчик ошибок драйвера
@app.exception_handler(AtolDriverError)
async def atol_driver_error_handler(request: Request, exc: AtolDriverError):
    """
    Обработчик ошибок драйвера АТОЛ
    """
    logger.error(f"ATOL Driver Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": "atol_driver_error"
        }
    )


# Общий обработчик исключений
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Обработчик общих исключений
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc),
            "type": "internal_error"
        }
    )


# Главный endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Корневой endpoint API
    """
    return {
        "name": "ATOL Driver API",
        "version": "1.0.0",
        "description": "REST API для работы с драйвером АТОЛ ККТ v.10",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Проверка состояния API
    """
    return {
        "status": "healthy",
        "service": "ATOL Driver API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
