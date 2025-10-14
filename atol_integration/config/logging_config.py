"""
Конфигурация логирования для драйвера АТОЛ v.10

Драйвер использует библиотеку log4cpp для логирования.
Настройки хранятся в файле fptr10_log.properties.
"""
import os
import platform
from pathlib import Path
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    """Уровни логирования"""
    ERROR = "ERROR"  # Только ошибки
    INFO = "INFO"  # Базовое логирование
    DEBUG = "DEBUG"  # Расширенное логирование


class LogCategory(Enum):
    """Категории логов драйвера"""
    FISCAL_PRINTER = "FiscalPrinter"  # Высокоуровневый лог работы с драйвером
    TRANSPORT = "Transport"  # Лог обмена драйвера с ККТ
    ETHERNET_OVER_TRANSPORT = "EthernetOverTransport"  # Лог канала обмена ККТ с интернетом
    DEVICE_DEBUG = "DeviceDebug"  # Отладочный вывод ККТ
    ONE_C = "1C"  # Лог интеграционного компонента 1С
    USB = "USB"  # Низкоуровневый лог обмена по USB
    COM = "COM"  # Низкоуровневый лог обмена по RS232/VCOM/TTY
    TCP = "TCP"  # Низкоуровневый лог обмена по TCP/IP
    BLUETOOTH = "Bluetooth"  # Низкоуровневый лог обмена по Bluetooth
    WEB = "Web"  # Логи Web-сервера ККТ


class LoggingConfig:
    """Управление конфигурацией логирования драйвера АТОЛ"""

    def __init__(self):
        """Инициализация конфигурации логирования"""
        self.work_directory = self._get_work_directory()
        self.log_directory = self.work_directory / "logs"
        self.config_file = self.work_directory / "fptr10_log.properties"

    @staticmethod
    def _get_work_directory() -> Path:
        """
        Получить рабочий каталог драйвера в зависимости от ОС

        Returns:
            Path: Путь к рабочему каталогу
        """
        system = platform.system()
        home = Path.home()

        if system == "Windows":
            # %APPDATA%/ATOL/drivers10/
            return Path(os.environ.get("APPDATA", home)) / "ATOL" / "drivers10"
        elif system == "Darwin":  # MacOS
            # ~/Library/Application Support/ru.atol.drivers10/
            return home / "Library" / "Application Support" / "ru.atol.drivers10"
        elif system == "Linux":
            # ~/.atol/drivers10/
            return home / ".atol" / "drivers10"
        else:
            # Для других систем используем домашний каталог
            return home / ".atol" / "drivers10"

    def ensure_directories(self) -> None:
        """Создать необходимые каталоги, если они не существуют"""
        self.work_directory.mkdir(parents=True, exist_ok=True)
        self.log_directory.mkdir(parents=True, exist_ok=True)

    def create_default_config(self) -> str:
        """
        Создать файл конфигурации логирования по умолчанию

        Returns:
            str: Путь к созданному файлу конфигурации
        """
        self.ensure_directories()

        # Шаблон конфигурации по умолчанию
        config_content = f"""# Конфигурация логирования драйвера АТОЛ v.10
# Автоматически сгенерирован

# Корневая категория
log4cpp.rootCategory=ERROR, file

# Категории логирования
log4cpp.category.FiscalPrinter=INFO, file
log4cpp.category.Transport=INFO, file
log4cpp.category.EthernetOverTransport=INFO, ofd
log4cpp.category.DeviceDebug=INFO, device_debug
log4cpp.category.1C=INFO, file1C

# Консольный вывод (для разработки)
log4cpp.appender.console=ConsoleAppender
log4cpp.appender.console.layout=PatternLayout
log4cpp.appender.console.layout.ConversionPattern=%d{{%Y.%m.%d %H:%M:%S.%l}} T:%t %-5p [%c] %m%n

# Основной лог файл
log4cpp.appender.file=DailyRollingFileAppender
log4cpp.appender.file.fileName={self.log_directory}/fptr10.log
log4cpp.appender.file.maxDaysKeep=14
log4cpp.appender.file.layout=PatternLayout
log4cpp.appender.file.layout.ConversionPattern=%d{{%Y.%m.%d %H:%M:%S.%l}} T:%t %-5p [%c] %L %m%n

# Лог обмена с ОФД
log4cpp.appender.ofd=DailyRollingFileAppender
log4cpp.appender.ofd.fileName={self.log_directory}/ofd.log
log4cpp.appender.ofd.maxDaysKeep=14
log4cpp.appender.ofd.layout=PatternLayout
log4cpp.appender.ofd.layout.ConversionPattern=%d{{%Y.%m.%d %H:%M:%S.%l}} T:%t %-5p [%c] %m%n

# Отладочный лог устройства
log4cpp.appender.device_debug=DailyRollingFileAppender
log4cpp.appender.device_debug.fileName={self.log_directory}/device_debug.log
log4cpp.appender.device_debug.maxDaysKeep=14
log4cpp.appender.device_debug.layout=PatternLayout
log4cpp.appender.device_debug.layout.ConversionPattern=%d{{%Y.%m.%d %H:%M:%S.%l}} T:%t %-5p [%c] %m%n

# Лог 1С
log4cpp.appender.file1C=DailyRollingFileAppender
log4cpp.appender.file1C.fileName={self.log_directory}/fptr1C.log
log4cpp.appender.file1C.maxDaysKeep=14
log4cpp.appender.file1C.layout=PatternLayout
log4cpp.appender.file1C.layout.ConversionPattern=%d{{%Y.%m.%d %H:%M:%S.%l}} T:%t %-5p [%c] %m%n
"""

        # Записываем конфигурацию в файл
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        return str(self.config_file)

    def set_custom_config_path(self, path: str) -> None:
        """
        Установить пользовательский путь к файлу конфигурации через переменную окружения

        Args:
            path: Полный путь к файлу fptr10_log.properties

        Note:
            Работает только на Windows, Linux и MacOS
        """
        if platform.system() in ["Windows", "Linux", "Darwin"]:
            os.environ["DTO10_LOG_CONFIG_FILE"] = path
        else:
            raise OSError(f"Установка пользовательского пути не поддерживается на {platform.system()}")

    def update_category_level(self, category: LogCategory, level: LogLevel) -> None:
        """
        Обновить уровень логирования для категории

        Args:
            category: Категория лога
            level: Уровень логирования
        """
        if not self.config_file.exists():
            self.create_default_config()

        # Читаем текущую конфигурацию
        with open(self.config_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Обновляем уровень для категории
        category_line = f"log4cpp.category.{category.value}="
        updated = False

        for i, line in enumerate(lines):
            if line.startswith(category_line):
                # Сохраняем appender-ы, меняем только уровень
                parts = line.split("=", 1)[1].strip().split(",", 1)
                if len(parts) == 2:
                    appenders = parts[1].strip()
                    lines[i] = f"{category_line}{level.value}, {appenders}\n"
                else:
                    lines[i] = f"{category_line}{level.value}\n"
                updated = True
                break

        # Если категория не найдена, добавляем её
        if not updated:
            lines.append(f"{category_line}{level.value}, file\n")

        # Записываем обновлённую конфигурацию
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def enable_console_logging(self, categories: Optional[list[LogCategory]] = None) -> None:
        """
        Включить вывод логов в консоль для указанных категорий

        Args:
            categories: Список категорий (если None, применяется ко всем)
        """
        if not self.config_file.exists():
            self.create_default_config()

        if categories is None:
            categories = list(LogCategory)

        # Читаем текущую конфигурацию
        with open(self.config_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Добавляем console к appender-ам категорий
        for category in categories:
            category_line = f"log4cpp.category.{category.value}="

            for i, line in enumerate(lines):
                if line.startswith(category_line):
                    if "console" not in line:
                        lines[i] = line.rstrip() + ", console\n"
                    break

        # Записываем обновлённую конфигурацию
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def get_log_files(self) -> list[Path]:
        """
        Получить список файлов логов

        Returns:
            list[Path]: Список путей к файлам логов
        """
        if not self.log_directory.exists():
            return []

        return sorted(self.log_directory.glob("*.log"))

    def clear_old_logs(self, days: int = 14) -> int:
        """
        Удалить старые лог-файлы

        Args:
            days: Количество дней для хранения логов

        Returns:
            int: Количество удалённых файлов
        """
        import time

        if not self.log_directory.exists():
            return 0

        current_time = time.time()
        cutoff_time = current_time - (days * 86400)  # 86400 секунд в дне
        deleted_count = 0

        for log_file in self.get_log_files():
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1

        return deleted_count


# Глобальный экземпляр конфигурации
logging_config = LoggingConfig()
