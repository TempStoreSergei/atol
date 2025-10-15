"""
REST API endpoint'ы для операций с кассирами и документами
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..api.redis_client import RedisClient, get_redis_client


router = APIRouter(prefix="/operator", tags=["Operator & Document Operations"])


# ========== МОДЕЛИ ДАННЫХ ==========

class OperatorLoginRequest(BaseModel):
    """Регистрация кассира"""
    operator_name: str = Field(..., description="ФИО кассира", max_length=255)
    operator_vatin: Optional[str] = Field(None, description="ИНН кассира (12 цифр)", max_length=12)


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ========== РЕГИСТРАЦИЯ КАССИРА ==========

@router.post("/login", response_model=StatusResponse)
async def operator_login(
    request: OperatorLoginRequest,
    redis: RedisClient = Depends(get_redis_client)
):
    """
    Зарегистрировать кассира (operatorLogin).

    **Обязательные параметры:**
    - **operator_name**: ФИО кассира (реквизит 1021)

    **Опциональные параметры:**
    - **operator_vatin**: ИНН кассира (реквизит 1203)

    **Важно:** Рекомендуется вызывать данный метод **перед каждой фискальной операцией**
    (открытие чека, печать отчета и т.д.).

    **Примеры:**
    ```json
    // С ИНН
    {"operator_name": "Кассир Иванов И.", "operator_vatin": "123456789047"}

    // Без ИНН
    {"operator_name": "Кассир Иванов И."}
    ```

    **Использование:**
    1. Регистрация перед открытием чека:
    ```
    POST /operator/login
    POST /receipt/open
    ```

    2. Регистрация перед печатью отчета:
    ```
    POST /operator/login
    POST /shift/close
    ```
    """
    return redis.execute_command('operator_login', request.model_dump(exclude_none=True))


# ========== ОПЕРАЦИИ С ДОКУМЕНТАМИ ==========

@router.post("/continue-print", response_model=StatusResponse)
async def continue_print(redis: RedisClient = Depends(get_redis_client)):
    """
    Допечатать документ (continuePrint).

    Используется для допечатывания фискального документа, который не был допечатан
    из-за проблем с принтером (закончилась бумага, открыта крышка и т.д.).

    **Когда использовать:**
    - После проверки состояния документа методом `/operator/check-document-closed`,
      если получен флаг `document_printed: false`
    - Автоматически допечатывается при следующей печатной операции, если не вызвать вручную

    **Важно:**
    - Метод не возвращает ошибки, если нет документов для допечатывания
    - Безопасно вызывать в любое время

    **Пример использования:**
    ```
    # 1. Закрыли чек
    POST /receipt/close

    # 2. Проверили состояние
    POST /operator/check-document-closed
    # Получили: {"document_closed": true, "document_printed": false}

    # 3. Устранили проблему (вставили бумагу)

    # 4. Допечатали документ
    POST /operator/continue-print
    ```
    """
    return redis.execute_command('continue_print')


@router.post("/check-document-closed", response_model=StatusResponse)
async def check_document_closed(redis: RedisClient = Depends(get_redis_client)):
    """
    Проверить закрытие документа (checkDocumentClosed).

    **Важнейший метод для обеспечения надежности!**

    Проверяет, был ли документ успешно закрыт в ФН и напечатан на чековой ленте.
    Используется после операций закрытия документов для контроля состояния.

    **Возвращает:**
    - **document_closed**: Документ закрылся в ФН (bool)
    - **document_printed**: Документ напечатался (bool)

    **Применим для:**
    - Чеков (продажи, возвраты, коррекции)
    - Отчетов закрытия и открытия смены
    - Отчетов регистрации, перерегистрации ККТ, закрытия ФН
    - Отчета о состоянии расчетов

    **Алгоритм обработки:**
    ```python
    # 1. Закрываем документ
    response = POST /receipt/close

    # 2. Проверяем состояние
    check = POST /operator/check-document-closed

    if not check['data']['document_closed']:
        # Документ не закрылся - отменяем и формируем заново
        POST /receipt/cancel
        return

    if not check['data']['document_printed']:
        # Документ закрылся, но не напечатался
        # Устраняем проблему с принтером (вставляем бумагу)
        # Допечатываем
        POST /operator/continue-print
    ```

    **Критические ситуации:**
    - Если метод вернул **ошибку** - состояние документа неизвестно!
    - Возможные причины: нарушение обмена Драйвер-ККТ или ККТ-ФН
    - **Действия**: Не выключать ПК, проверить физическое подключение,
      возможно потребуется перезагрузка ККТ

    **Пример ответа:**
    ```json
    {
      "success": true,
      "message": "Состояние документа проверено",
      "data": {
        "document_closed": true,
        "document_printed": true
      }
    }
    ```
    """
    return redis.execute_command('check_document_closed')
