"""
Валидаторы данных
"""
import re


def validate_inn(inn: str) -> bool:
    """Проверка ИНН"""
    return bool(re.match(r'^\d{10}$|^\d{12}$', inn))


def validate_email(email: str) -> bool:
    """Проверка email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Проверка телефона"""
    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10
