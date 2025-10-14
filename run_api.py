"""
Скрипт для запуска FastAPI сервера АТОЛ Driver API
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "atol_integration.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
