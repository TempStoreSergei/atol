"""
REST API endpoint'ы для нефискальной печати
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field

from ..api.driver import AtolDriver, AtolDriverError
from ..api import libfptr10
IFptr = libfptr10.IFptr

router = APIRouter(prefix="/print", tags=["Non-Fiscal Printing"])

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

class PrintTextRequest(BaseModel):
    """Запрос на печать текста"""
    text: str = Field(..., description="Текст для печати")
    alignment: int = Field(0, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")
    wrap: int = Field(0, description="Перенос строк (0=нет, 1=по словам, 2=по символам)")
    font: int = Field(0, description="Номер шрифта")
    double_width: bool = Field(False, description="Двойная ширина")
    double_height: bool = Field(False, description="Двойная высота")
    format_text: bool = Field(False, description="Форматированная строка с управляющими символами")


class PrintBarcodeRequest(BaseModel):
    """Запрос на печать штрихкода"""
    barcode: str = Field(..., description="Данные штрихкода")
    barcode_type: int = Field(IFptr.LIBFPTR_BT_QR, description="Тип штрихкода")
    alignment: int = Field(0, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")
    scale: int = Field(2, description="Коэффициент увеличения (1-10)")
    height: Optional[int] = Field(None, description="Высота одномерного ШК в пикселях")
    print_text: bool = Field(True, description="Печатать данные под ШК (для одномерных)")
    correction: int = Field(0, description="Уровень коррекции ошибок")


class PrintPictureRequest(BaseModel):
    """Запрос на печать картинки"""
    filename: str = Field(..., description="Путь к файлу картинки (bmp/png)")
    alignment: int = Field(0, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")
    scale_percent: int = Field(100, description="Масштаб в процентах")


class PrintPictureByNumberRequest(BaseModel):
    """Запрос на печать картинки из памяти ККТ"""
    picture_number: int = Field(..., description="Номер картинки в памяти ККТ")
    alignment: int = Field(1, description="Выравнивание (0=влево, 1=по центру, 2=вправо)")


class StatusResponse(BaseModel):
    """Статус операции"""
    success: bool
    message: Optional[str] = None


# ========== УПРАВЛЕНИЕ НЕФИСКАЛЬНЫМ ДОКУМЕНТОМ ==========

@router.post("/document/begin")
async def begin_nonfiscal_document():
    """
    Открыть нефискальный документ (fptr.beginNonfiscalDocument)

    Открывает нефискальный документ для печати. Рекомендуется всегда
    печатать информацию внутри документа (чека или нефискального).
    """
    check_driver()

    try:
        result = driver.fptr.beginNonfiscalDocument()

        if result < 0:
            raise AtolDriverError(f"Ошибка открытия нефискального документа: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Нефискальный документ открыт"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/document/end")
async def end_nonfiscal_document(print_footer: bool = True):
    """
    Закрыть нефискальный документ (fptr.endNonfiscalDocument)

    Args:
        print_footer: Печатать подвал документа (клише)
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PRINT_FOOTER, print_footer)
        result = driver.fptr.endNonfiscalDocument()

        if result < 0:
            raise AtolDriverError(f"Ошибка закрытия нефискального документа: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Нефискальный документ закрыт"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ПЕЧАТЬ КЛИШЕ ==========

@router.post("/cliche")
async def print_cliche():
    """
    Напечатать клише (fptr.printCliche)

    Печатает запрограммированное в ККТ клише (шапку/подвал).
    Клише автоматически печатается при закрытии документов.
    """
    check_driver()

    try:
        result = driver.fptr.printCliche()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати клише: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Клише напечатано"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ПЕЧАТЬ ТЕКСТА ==========

@router.post("/text")
async def print_text(request: PrintTextRequest):
    """
    Напечатать текст (fptr.printText)

    Печатает текстовую строку с возможностью форматирования.

    Управляющие символы для форматированного текста (format_text=true):
    - \\n - перевод строки
    - \\sXNN - вставить символ X NN раз (например: \\s=05 -> "=====")
    - \\lNN - промотать NN пиксельных линий
    - \\fNN - выбрать шрифт NN
    - \\aX - выравнивание (l=влево, c=центр, r=вправо)
    - \\hN - умножение высоты (1 или 2)
    - \\wN - умножение ширины (1 или 2)
    - \\z - сброс форматирования
    - \\pNN - печать картинки номер NN
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, request.text)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, request.alignment)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT_WRAP, request.wrap)

        if not request.format_text:
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT, request.font)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_WIDTH, request.double_width)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT, request.double_height)

        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FORMAT_TEXT, request.format_text)

        result = driver.fptr.printText()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати текста: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Текст напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/feed")
async def feed_line(lines: int = 1):
    """
    Промотать ленту (пустые строки)

    Args:
        lines: Количество пустых строк для промотки
    """
    check_driver()

    try:
        for _ in range(lines):
            result = driver.fptr.printText()
            if result < 0:
                raise AtolDriverError(f"Ошибка промотки ленты: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message=f"Лента промотана на {lines} строк"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ПЕЧАТЬ ШТРИХКОДА ==========

@router.post("/barcode")
async def print_barcode(request: PrintBarcodeRequest):
    """
    Напечатать штрихкод (fptr.printBarcode)

    Типы штрихкодов:
    - Одномерные: EAN8, EAN13, UPC-A, UPC-E, Code39, Code93, Code128,
      Codabar, ITF, ITF-14, GS1-128, Code39 Extended
    - Двумерные: QR, PDF417, AZTEC

    Коды типов штрихкодов:
    - LIBFPTR_BT_EAN_8 = 8
    - LIBFPTR_BT_EAN_13 = 9
    - LIBFPTR_BT_CODE_39 = 10
    - LIBFPTR_BT_CODE_128 = 12
    - LIBFPTR_BT_QR = 17
    - LIBFPTR_BT_PDF417 = 18
    - LIBFPTR_BT_AZTEC = 19
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, request.barcode)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, request.barcode_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, request.alignment)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, request.scale)

        # Параметры для одномерных штрихкодов
        if request.barcode_type < 17:  # Одномерные ШК
            if request.height:
                driver.fptr.setParam(IFptr.LIBFPTR_PARAM_HEIGHT, request.height)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_PRINT_TEXT, request.print_text)

        # Параметры для QR и других 2D
        if request.barcode_type >= 17:
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_CORRECTION, request.correction)

        result = driver.fptr.printBarcode()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати штрихкода: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Штрихкод напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ПЕЧАТЬ КАРТИНОК ==========

@router.post("/picture")
async def print_picture(request: PrintPictureRequest):
    """
    Напечатать картинку из файла (fptr.printPicture)

    Поддерживаются форматы: BMP, PNG (без прозрачности)
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FILENAME, request.filename)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, request.alignment)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE_PERCENT, request.scale_percent)

        result = driver.fptr.printPicture()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати картинки: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="Картинка напечатана"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/picture-by-number")
async def print_picture_by_number(request: PrintPictureByNumberRequest):
    """
    Напечатать картинку из памяти ККТ (fptr.printPictureByNumber)

    Печатает картинку, заранее загруженную в память ККТ по номеру.
    """
    check_driver()

    try:
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PICTURE_NUMBER, request.picture_number)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, request.alignment)

        result = driver.fptr.printPictureByNumber()

        if result < 0:
            raise AtolDriverError(f"Ошибка печати картинки из памяти: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message=f"Картинка #{request.picture_number} напечатана"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== СЛОЖНАЯ ПЕЧАТЬ ==========

@router.post("/text-with-barcode")
async def print_text_with_barcode(
    barcode: str,
    barcode_type: int = IFptr.LIBFPTR_BT_QR,
    text_lines: list[str] = [],
    scale: int = 4
):
    """
    Напечатать текст рядом со штрихкодом (LIBFPTR_DEFER_OVERLAY)

    Печатает текстовые строки справа от QR-кода.
    Работает только с QR-кодами.

    Args:
        barcode: Данные QR-кода
        barcode_type: Тип штрихкода (по умолчанию QR)
        text_lines: Список строк текста для печати справа от QR
        scale: Масштаб QR-кода
    """
    check_driver()

    try:
        # Добавляем текстовые строки с флагом отложенной печати
        for line in text_lines:
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, line)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_RIGHT)
            driver.fptr.setParam(IFptr.LIBFPTR_PARAM_DEFER, IFptr.LIBFPTR_DEFER_OVERLAY)

            result = driver.fptr.printText()
            if result < 0:
                raise AtolDriverError(f"Ошибка добавления текста: {driver.fptr.errorDescription()}")

        # Печатаем QR-код
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, barcode)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, barcode_type)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_LEFT)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, scale)

        result = driver.fptr.printBarcode()
        if result < 0:
            raise AtolDriverError(f"Ошибка печати QR-кода: {driver.fptr.errorDescription()}")

        return StatusResponse(
            success=True,
            message="QR-код с текстом напечатан"
        )

    except AtolDriverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ========== ПОЛНЫЙ ПРИМЕР НЕФИСКАЛЬНОЙ ПЕЧАТИ ==========

@router.post("/example-nonfiscal")
async def print_nonfiscal_example():
    """
    Пример нефискального документа

    Демонстрирует печать нефискального документа с различными элементами:
    - Клише
    - Текст с форматированием
    - Штрихкод
    - Промотка ленты
    """
    check_driver()

    try:
        # Открываем нефискальный документ
        driver.fptr.beginNonfiscalDocument()

        # Печатаем клише
        driver.fptr.printCliche()

        # Промотка
        driver.fptr.printText()

        # Заголовок
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, "НЕФИСКАЛЬНЫЙ ЧЕК")
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_CENTER)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT, True)
        driver.fptr.printText()

        # Разделитель
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, "================================")
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_LEFT)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_FONT_DOUBLE_HEIGHT, False)
        driver.fptr.printText()

        # Информация
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, "Пример печати нефискального документа")
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_LEFT)
        driver.fptr.printText()

        # Промотка
        driver.fptr.printText()

        # QR-код
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE, "https://example.com")
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_BARCODE_TYPE, IFptr.LIBFPTR_BT_QR)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_ALIGNMENT, IFptr.LIBFPTR_ALIGNMENT_CENTER)
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_SCALE, 3)
        driver.fptr.printBarcode()

        # Закрываем документ с печатью подвала
        driver.fptr.setParam(IFptr.LIBFPTR_PARAM_PRINT_FOOTER, True)
        driver.fptr.endNonfiscalDocument()

        return StatusResponse(
            success=True,
            message="Пример нефискального документа напечатан"
        )

    except AtolDriverError as e:
        # При ошибке пытаемся закрыть документ
        try:
            driver.fptr.endNonfiscalDocument()
        except:
            pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
