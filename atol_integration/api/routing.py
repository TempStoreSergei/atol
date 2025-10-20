"""
Модели и фабрики для динамической настройки роутинга FastAPI
"""
from typing import Callable, List, Type
from pydantic import BaseModel, Field
from fastapi import APIRouter


class RouteDTO(BaseModel):
    """
    DTO для описания маршрута API

    Attributes:
        path: Путь эндпоинта (например, "/open")
        endpoint: Функция-обработчик эндпоинта
        response_model: Pydantic модель для ответа (опционально)
        methods: HTTP методы (по умолчанию ["POST"])
        status_code: HTTP статус код успешного ответа (по умолчанию 200)
        summary: Краткое описание эндпоинта
        description: Полное описание эндпоинта
        responses: Дополнительные варианты ответов для OpenAPI документации
    """
    path: str
    endpoint: Callable
    response_model: Type[BaseModel] | None = None
    methods: List[str] = Field(default_factory=lambda: ["POST"])
    status_code: int = 200
    summary: str = ""
    description: str = ""
    responses: dict[int, dict] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class RouterFactory:
    """
    Фабрика для создания роутеров FastAPI с декларативной конфигурацией

    Example:
        >>> router_factory = RouterFactory(
        ...     prefix='/api/v1/receipt',
        ...     tags=['Чеки'],
        ...     routes=RECEIPT_ROUTES,
        ... )
        >>> app.include_router(router_factory())
    """

    def __init__(
        self,
        prefix: str,
        tags: list[str],
        routes: list[RouteDTO] | None = None
    ):
        """
        Args:
            prefix: Префикс для всех маршрутов в роутере
            tags: Теги для группировки эндпоинтов в OpenAPI документации
            routes: Список RouteDTO с описанием маршрутов
        """
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.routes = routes
        if routes:
            self._setup_router()

    def _setup_router(self):
        """Регистрация всех маршрутов в роутере"""
        for route in self.routes:
            self.router.add_api_route(
                path=route.path,
                endpoint=route.endpoint,
                response_model=route.response_model,
                status_code=route.status_code,
                methods=route.methods,
                summary=route.summary,
                description=route.description,
                responses=route.responses,
            )

    def __call__(self) -> APIRouter:
        """Возвращает настроенный роутер для подключения к FastAPI приложению"""
        return self.router
