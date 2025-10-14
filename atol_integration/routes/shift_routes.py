"""
REST API endpoint'ы для операций со сменами (shifts)
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..api.driver import AtolDriver, AtolDriverError
from ..api import libfptr10
IFptr = libfptr10.IFptr

router = APIRouter(prefix="/shift", tags=["Shift"])

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

class OpenShiftRequest(BaseModel):
    """Запрос на открытие смены"""
    cashier_name: str = Field(..., description="Имя кассира")


class CloseShiftResponse(BaseModel):
    """Ответ на закрытие смены с данными"""
    success: bool
    shift_number: Optional[int] = None
    fiscal_document_number: Optional[int] = None
    fiscal_document_sign: Optional[int] = None
    fiscal_storage_number: Optional[str] = None
    total_receipts: Optional[int] = None
    message: Optional[str] = None


class ShiftStatusResponse(BaseModel):
    """Статус смены"""
    shift_opened: bool
    shift_number: Optional[int] = None
    shift_expired: bool = False
    hours_since_open: Optional[int] = None
    receipts_count: Optional[int] = None


class XReportResponse(BaseModel):
    """Ответ на X-отчет"""
    success: bool
    shift_number: Optional[int] = None
    receipts_count: Optional[int] = None
    total_sales: Optional[float] = None
    total_returns: Optional[float] = None
    cash_in_drawer: Optional[float] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== ОСНОВНЫЕ ОПЕРАЦИИ СО СМЕНАМИ ==========

@router.post("/open")
async def open_shift(request: OpenShiftRequest):
    """
    Открыть новую смену (fptr.openShift)

    Открывает новую рабочую смену на кассе.
    Смена должна быть открыта перед началом работы с чеками.
    """
    check_driver()

    try:
        # Устанавливаем имя кассира
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, request.cashier_name)

        # Открываем смену
        result = driver.fptr.openShift()

        if result < 0:
            raise AtolDriverError(f"Ошибка открытия смены: {driver.fptr.errorDescription()}")

        # Получаем номер смены
        shift_number = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)

        return StatusResponse(
            success=True,
            message=f"Смена #{shift_number} успешно открыта"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/close", response_model=CloseShiftResponse)
async def close_shift(cashier_name: str):
    """
    Закрыть текущую смену (Z-отчет) (fptr.closeShift)

    Закрывает текущую смену и печатает Z-отчет.
    После закрытия смены необходимо открыть новую смену для продолжения работы.
    """
    check_driver()

    try:
        # Устанавливаем имя кассира
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)

        # Закрываем смену (печатаем Z-отчет)
        result = driver.fptr.closeShift()

        if result < 0:
            raise AtolDriverError(f"Ошибка закрытия смены: {driver.fptr.errorDescription()}")

        # Получаем данные о закрытой смене
        return CloseShiftResponse(
            success=True,
            shift_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            fiscal_document_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_NUMBER),
            fiscal_document_sign=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FISCAL_DOCUMENT_SIGN),
            fiscal_storage_number=driver.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_STORAGE_NUMBER),
            message="Смена успешно закрыта, Z-отчет напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=ShiftStatusResponse)
async def get_shift_status():
    """
    Получить статус текущей смены (queryData LIBFPTR_DT_SHIFT_STATE)

    Возвращает информацию о состоянии смены:
    - Открыта ли смена
    - Номер смены
    - Количество чеков
    - Срок смены (истек ли 24-часовой период)
    """
    check_driver()

    try:
        # Запрашиваем состояние смены
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
        result = driver.fptr.queryData()

        if result < 0:
            raise AtolDriverError(f"Ошибка запроса статуса смены: {driver.fptr.errorDescription()}")

        # Получаем данные о смене
        shift_state = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE)
        shift_opened = (shift_state == 1 or shift_state == 3)
        shift_expired = (shift_state == 3)

        return ShiftStatusResponse(
            shift_opened=shift_opened,
            shift_number=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER),
            shift_expired=shift_expired,
            hours_since_open=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_TIME) if shift_opened else None,
            receipts_count=driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER) if shift_opened else None
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/x-report", response_model=XReportResponse)
async def print_x_report(cashier_name: str):
    """
    Напечатать X-отчет (отчет без гашения) (fptr.report)

    Печатает отчет о текущем состоянии смены без закрытия смены.
    Используется для контроля текущих продаж в течение смены.
    """
    check_driver()

    try:
        # Устанавливаем имя кассира
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)

        # Устанавливаем тип отчета - X-отчет (без гашения)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_X)

        # Печатаем отчет
        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати X-отчета: {driver.fptr.errorDescription()}")

        # Получаем данные из отчета
        shift_number = driver.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)

        return XReportResponse(
            success=True,
            shift_number=shift_number,
            message=f"X-отчет для смены #{shift_number} успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ДОПОЛНИТЕЛЬНЫЕ ОТЧЕТЫ ==========

@router.post("/report-by-departments")
async def print_report_by_departments(cashier_name: str):
    """
    Напечатать отчет по секциям (fptr.report с LIBFPTR_RT_DEPARTMENTS)

    Печатает отчет о продажах в разрезе секций (отделов) кассы.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_DEPARTMENTS)

        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати отчета по секциям: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Отчет по секциям успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/report-by-taxes")
async def print_report_by_taxes(cashier_name: str):
    """
    Напечатать отчет по налогам (fptr.report с LIBFPTR_RT_TAXES)

    Печатает отчет о продажах в разрезе налоговых ставок.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_TAXES)

        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати отчета по налогам: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Отчет по налогам успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/report-by-cashiers")
async def print_report_by_cashiers(cashier_name: str):
    """
    Напечатать отчет по кассирам (fptr.report с LIBFPTR_RT_CASHIERS)

    Печатает отчет о продажах в разрезе кассиров.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CASHIERS)

        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати отчета по кассирам: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Отчет по кассирам успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/report-by-hours")
async def print_report_by_hours(cashier_name: str):
    """
    Напечатать почасовой отчет (fptr.report с LIBFPTR_RT_HOURS)

    Печатает отчет о продажах в разрезе часов работы.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_HOURS)

        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати почасового отчета: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Почасовой отчет успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/report-by-goods")
async def print_report_by_goods(cashier_name: str):
    """
    Напечатать отчет по товарам (fptr.report с LIBFPTR_RT_GOODS)

    Печатает отчет о продажах в разрезе товаров.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_OPERATOR_NAME, cashier_name)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_GOODS)

        result = driver.fptr.report()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати отчета по товарам: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Отчет по товарам успешно напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
