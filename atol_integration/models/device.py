"""
Модели данных для устройств
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """Информация об устройстве ККТ"""
    serial_number: str
    factory_number: str
    model: str
    firmware_version: str
    registration_number: Optional[str] = None
    fiscal_drive_number: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict):
        """Создать из словаря"""
        # TODO: Реализовать маппинг
        pass
