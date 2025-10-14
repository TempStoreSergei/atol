"""
REST API endpoint'ы для кассовых операций (cash operations)
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..api.driver import AtolDriver, AtolDriverError
from ..api import libfptr10
IFptr = libfptr10.IFptr

router = APIRouter(prefix="/cash", tags=["Cash Operations"])

# Глобальный экземпляр драйвера (будет установлен из server.py)
driver: Optional[AtolDriver] = None


def set_driver(drv: AtolDriver):
    """Установить экземпляр драйвера для использования в routes"""
    global driver
    driver = drv


def check_driver():
    """Проверить что драйвер инициализирован"""
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Driver not initialized"
        )


# ========== МОДЕЛИ ДАННЫХ ==========

class CashOperationRequest(BaseModel):
    """Запрос на операцию с наличными"""
    amount: float = Field(..., description="Сумма операции", gt=0)
    cashier_name: str = Field(..., description="Имя кассира")


class CashOperationResponse(BaseModel):
    """Ответ на операцию с наличными"""
    success: bool
    operation_type: str
    amount: float
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    shift_number: Optional[int] = None
    message: Optional[str] = None


class CashSumResponse(BaseModel):
    """Ответ с суммой наличных в ящике"""
    cash_sum: float
    currency: str = "RUB"


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ОПЕРАЦИИ С НАЛИЧНЫМИ ==========

@router.post("/in", response_model=CashOperationResponse)
async def cash_in(request: CashOperationRequest):
    """
    Внесение наличных в кассу (fptr.cashIncome)

    Регистрирует внесение наличных денежных средств в денежный ящик.
    Печатается соответствующий фискальный документ.

    Пример использования:
    - Инкассация
    - Внесение выручки от другой кассы
    - Размен
    """
    check_driver()

    try:
        # Устанавливаем параметры операции
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, request.amount)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, request.cashier_name)

        # Выполняем внесение
        result = driver.fptr.cashIncome()

        if result < 0:
            raise AtolDriverError(f"Ошибка внесения наличных: {driver.fptr.errorDescription()}")

        # Получаем фискальные данные
        return CashOperationResponse(
            success=True,
            operation_type="cash_in",
            amount=request.amount,
            fiscal_document_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
            fiscal_document_sign=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
            shift_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            message=f"Внесение {request.amount:.2f} руб. успешно выполнено"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/out", response_model=CashOperationResponse)
async def cash_out(request: CashOperationRequest):
    """
    Изъятие наличных из кассы (fptr.cashOutcome)

    Регистрирует изъятие наличных денежных средств из денежного ящика.
    Печатается соответствующий фискальный документ.

    Пример использования:
    - Инкассация
    - Передача выручки в банк
    - Изъятие излишков
    """
    check_driver()

    try:
        # Устанавливаем параметры операции
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, request.amount)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, request.cashier_name)

        # Выполняем изъятие
        result = driver.fptr.cashOutcome()

        if result < 0:
            raise AtolDriverError(f"Ошибка изъятия наличных: {driver.fptr.errorDescription()}")

        # Получаем фискальные данные
        return CashOperationResponse(
            success=True,
            operation_type="cash_out",
            amount=request.amount,
            fiscal_document_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
            fiscal_document_sign=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
            shift_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            message=f"Изъятие {request.amount:.2f} руб. успешно выполнено"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sum", response_model=CashSumResponse)
async def get_cash_sum():
    """
    Получить сумму наличных в денежном ящике (queryData LIBFPTR_DT_CASH_SUM)

    Запрашивает текущую сумму наличных денег в денежном ящике кассы.
    Это не запрос остатка в ФН, а именно сумма по счетчикам кассы.
    """
    check_driver()

    try:
        # Запрашиваем сумму наличных
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASH_SUM)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса суммы наличных: {driver.fptr.errorDescription()}")

        # Получаем сумму
        cash_sum = driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)

        return CashSumResponse(cash_sum=cash_sum)

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== УПРАВЛЕНИЕ ДЕНЕЖНЫМ ЯЩИКОМ ==========

@router.post("/drawer/open")
async def open_cash_drawer():
    """
    Открыть денежный ящик (fptr.openCashDrawer)

    Посылает импульс на открытие денежного ящика без печати документа.
    Используется для немедленного доступа к деньгам без фискальной операции.

    Примечание: Не все модели ККТ поддерживают эту функцию.
    """
    check_driver()

    try:
        result = driver.fptr.openCashDrawer()

        if result < 0:
            raise AtolDriverError(f"Ошибка открытия денежного ящика: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Команда на открытие денежного ящика отправлена"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/drawer/status")
async def get_cash_drawer_status():
    """
    Проверить состояние денежного ящика (queryData LIBFPTR_DT_STATUS)

    Возвращает информацию о состоянии денежного ящика (открыт/закрыт).

    Примечание: Не все модели ККТ поддерживают датчик состояния ящика.
    """
    check_driver()

    try:
        # Запрашиваем статус устройства
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса статуса: {driver.fptr.errorDescription()}")

        # Получаем флаги состояния
        drawer_opened = driver.fptr.getParamBool(IFptr.LIBFPTR_PARAM_DRAWER_OPENED)

        return {
            "drawer_opened": drawer_opened,
            "message": "Денежный ящик открыт" if drawer_opened else "Денежный ящик закрыт"
        }

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СТАТИСТИКА ПО КАССОВЫМ ОПЕРАЦИЯМ ==========

@router.get("/statistics/cashin-sum")
async def get_cashin_sum():
    """
    Получить сумму внесений за смену (queryData LIBFPTR_DT_CASHIN_SUM)

    Возвращает общую сумму внесений наличных за текущую смену.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHIN_SUM)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса суммы внесений: {driver.fptr.errorDescription()}")

        cashin_sum = driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)

        return {"cashin_sum": cashin_sum, "currency": "RUB"}

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/statistics/cashout-sum")
async def get_cashout_sum():
    """
    Получить сумму изъятий за смену (queryData LIBFPTR_DT_CASHOUT_SUM)

    Возвращает общую сумму изъятий наличных за текущую смену.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHOUT_SUM)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса суммы изъятий: {driver.fptr.errorDescription()}")

        cashout_sum = driver.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_SUM)

        return {"cashout_sum": cashout_sum, "currency": "RUB"}

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/statistics/cashin-count")
async def get_cashin_count():
    """
    Получить количество внесений за смену (queryData LIBFPTR_DT_CASHIN_COUNT)

    Возвращает количество операций внесения наличных за текущую смену.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHIN_COUNT)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса количества внесений: {driver.fptr.errorDescription()}")

        cashin_count = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_COUNT)

        return {"cashin_count": cashin_count}

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/statistics/cashout-count")
async def get_cashout_count():
    """
    Получить количество изъятий за смену (queryData LIBFPTR_DT_CASHOUT_COUNT)

    Возвращает количество операций изъятия наличных за текущую смену.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_CASHOUT_COUNT)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса количества изъятий: {driver.fptr.errorDescription()}")

        cashout_count = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_COUNT)

        return {"cashout_count": cashout_count}

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
