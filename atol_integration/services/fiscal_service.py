"""
Сервис фискализации
"""
from typing import Dict, Any
from ..models.receipt import Receipt
from ..api.client import AtolClient


class FiscalService:
    """Сервис для работы с фискальными операциями"""

    def __init__(self, client: AtolClient):
        self.client = client

    def fiscalize_receipt(self, receipt: Receipt) -> Dict[str, Any]:
        """Фискализировать чек"""
        # TODO: Реализовать
        pass

    def get_fiscal_status(self, uuid: str) -> Dict[str, Any]:
        """Получить статус фискализации"""
        # TODO: Реализовать
        pass
