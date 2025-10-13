"""
Клиент для работы с API АТОЛ
"""
import requests
from typing import Optional, Dict, Any


class AtolClient:
    """Клиент для взаимодействия с АТОЛ Web API"""

    def __init__(self, base_url: str, login: str, password: str):
        self.base_url = base_url
        self.login = login
        self.password = password
        self.token: Optional[str] = None
        self.session = requests.Session()

    def get_token(self) -> str:
        """Получение токена авторизации"""
        # TODO: Реализовать получение токена
        pass

    def create_receipt(self, receipt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание чека"""
        # TODO: Реализовать создание чека
        pass

    def get_receipt_status(self, uuid: str) -> Dict[str, Any]:
        """Получение статуса чека"""
        # TODO: Реализовать получение статуса
        pass
