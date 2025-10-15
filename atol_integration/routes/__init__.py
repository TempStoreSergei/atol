"""
FastAPI routes для АТОЛ ККТ API

Экспортирует все роутеры для подключения к FastAPI приложению.
"""

from . import connection_routes
from . import receipt_routes
from . import shift_routes
from . import cash_routes
from . import query_routes
from . import print_routes
from . import config_routes

__all__ = [
    'connection_routes',
    'receipt_routes',
    'shift_routes',
    'cash_routes',
    'query_routes',
    'print_routes',
    'config_routes',
]
