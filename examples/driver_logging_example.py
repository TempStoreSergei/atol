"""
Пример настройки и использования логирования драйвера АТОЛ v.10

Демонстрирует:
- Создание файла конфигурации логирования
- Настройка уровней логирования для разных категорий
- Использование меток драйвера для разделения логов
- Включение консольного вывода
- Управление файлами логов
"""
import sys
import os

# Добавляем путь к модулю atol_integration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from atol_integration.api.driver import AtolDriver, ConnectionType, ReceiptType, TaxType, PaymentType
from atol_integration.config.logging_config import (
    LoggingConfig,
    LogLevel,
    LogCategory,
    logging_config
)


def setup_logging_example():
    """Пример настройки логирования"""
    print("=" * 60)
    print("Настройка логирования драйвера АТОЛ")
    print("=" * 60)

    # Создаём экземпляр конфигурации
    config = LoggingConfig()

    print(f"\nРабочий каталог: {config.work_directory}")
    print(f"Каталог логов: {config.log_directory}")
    print(f"Файл конфигурации: {config.config_file}")

    # Создаём файл конфигурации по умолчанию
    print("\n1. Создание файла конфигурации...")
    config_path = config.create_default_config()
    print(f"   Создан: {config_path}")

    # Настраиваем уровни логирования для разных категорий
    print("\n2. Настройка уровней логирования...")

    # Включаем DEBUG для основной работы драйвера
    config.update_category_level(LogCategory.FISCAL_PRINTER, LogLevel.DEBUG)
    print(f"   {LogCategory.FISCAL_PRINTER.value}: {LogLevel.DEBUG.value}")

    # Включаем INFO для транспорта
    config.update_category_level(LogCategory.TRANSPORT, LogLevel.INFO)
    print(f"   {LogCategory.TRANSPORT.value}: {LogLevel.INFO.value}")

    # Включаем DEBUG для отладки устройства
    config.update_category_level(LogCategory.DEVICE_DEBUG, LogLevel.DEBUG)
    print(f"   {LogCategory.DEVICE_DEBUG.value}: {LogLevel.DEBUG.value}")

    # Включаем консольный вывод для основных категорий
    print("\n3. Включение консольного вывода...")
    config.enable_console_logging([
        LogCategory.FISCAL_PRINTER,
        LogCategory.TRANSPORT
    ])
    print("   Консольный вывод включён для FiscalPrinter и Transport")

    print("\n✓ Конфигурация логирования завершена")
    print("=" * 60)


def driver_with_label_example():
    """Пример использования метки драйвера"""
    print("\n" + "=" * 60)
    print("Использование метки драйвера")
    print("=" * 60)

    try:
        # Создаём драйвер
        driver = AtolDriver()

        # Устанавливаем метку для этого экземпляра драйвера
        # Метка будет добавляться в каждую строку лога (если в формате есть %L)
        label = "КАССА-01"
        driver.change_label(label)
        print(f"\n✓ Метка драйвера установлена: {label}")

        # Все последующие операции будут логироваться с этой меткой
        print(f"\nВсе операции этого драйвера будут в логах с меткой [{label}]")

        # Пример: подключение с меткой
        print("\nПопытка подключения к ККТ (см. логи)...")
        try:
            driver.connect(
                connection_type=ConnectionType.TCP,
                host="192.168.1.100",
                port=5555
            )
        except Exception as e:
            print(f"   Ожидаемая ошибка (для демонстрации): {e}")

        print("\n✓ Проверьте файл логов - там будет метка " + label)

    except Exception as e:
        print(f"✗ Ошибка: {e}")

    print("=" * 60)


def multiple_drivers_example():
    """Пример работы с несколькими драйверами с разными метками"""
    print("\n" + "=" * 60)
    print("Работа с несколькими экземплярами драйвера")
    print("=" * 60)

    drivers = []

    try:
        # Создаём 3 драйвера для разных касс
        for i in range(1, 4):
            driver = AtolDriver()
            label = f"КАССА-{i:02d}"
            driver.change_label(label)
            drivers.append((driver, label))
            print(f"✓ Создан драйвер с меткой: {label}")

        print("\nКаждый драйвер будет писать логи с своей меткой,")
        print("что позволяет легко разделять логи разных касс.")

        # Пример операций с каждым драйвером
        print("\nПопытка подключения к каждой кассе...")
        for driver, label in drivers:
            print(f"\n  {label}:")
            try:
                driver.connect(
                    connection_type=ConnectionType.TCP,
                    host=f"192.168.1.{100 + int(label[-2:])}",
                    port=5555
                )
                print(f"    ✓ Подключено")
            except Exception as e:
                print(f"    ✗ Ошибка: {e}")

        print("\n✓ Проверьте файл логов - каждая операция будет")
        print("  помечена соответствующей меткой кассы")

    except Exception as e:
        print(f"✗ Ошибка: {e}")
    finally:
        # Отключаем все драйверы
        for driver, _ in drivers:
            try:
                driver.disconnect()
            except:
                pass

    print("=" * 60)


def log_management_example():
    """Пример управления файлами логов"""
    print("\n" + "=" * 60)
    print("Управление файлами логов")
    print("=" * 60)

    config = logging_config

    # Получаем список файлов логов
    log_files = config.get_log_files()

    if log_files:
        print(f"\nНайдено файлов логов: {len(log_files)}")
        for log_file in log_files:
            size_mb = log_file.stat().st_size / (1024 * 1024)
            print(f"  - {log_file.name} ({size_mb:.2f} MB)")
    else:
        print("\nФайлы логов не найдены")

    # Очистка старых логов (старше 14 дней)
    print("\nОчистка логов старше 14 дней...")
    deleted = config.clear_old_logs(days=14)
    print(f"  Удалено файлов: {deleted}")

    print("=" * 60)


def custom_config_path_example():
    """Пример использования пользовательского пути к конфигурации"""
    print("\n" + "=" * 60)
    print("Пользовательский путь к конфигурации")
    print("=" * 60)

    config = LoggingConfig()

    # Можно указать свой путь к файлу конфигурации
    # через переменную окружения DTO10_LOG_CONFIG_FILE
    custom_path = "/tmp/my_custom_fptr10_log.properties"

    print(f"\nУстановка пользовательского пути: {custom_path}")

    try:
        config.set_custom_config_path(custom_path)
        print("✓ Путь установлен")
        print("  Драйвер будет использовать эту конфигурацию")
        print(f"  Переменная окружения: DTO10_LOG_CONFIG_FILE={custom_path}")
    except OSError as e:
        print(f"✗ Ошибка: {e}")

    print("=" * 60)


def main():
    """Главная функция с примерами"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Примеры логирования АТОЛ Драйвер v.10" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")

    # 1. Настройка логирования
    setup_logging_example()

    # 2. Использование метки драйвера
    driver_with_label_example()

    # 3. Несколько драйверов с разными метками
    multiple_drivers_example()

    # 4. Управление логами
    log_management_example()

    # 5. Пользовательский путь к конфигурации
    custom_config_path_example()

    print("\n" + "=" * 60)
    print("Дополнительная информация:")
    print("=" * 60)
    print("\nРасположение файлов логирования:")
    print(f"  Windows:  %APPDATA%/ATOL/drivers10/")
    print(f"  Linux:    ~/.atol/drivers10/")
    print(f"  MacOS:    ~/Library/Application Support/ru.atol.drivers10/")

    print("\nФайлы логов:")
    print("  - fptr10.log       : Основной лог драйвера")
    print("  - ofd.log          : Лог обмена с ОФД")
    print("  - device_debug.log : Отладочная информация устройства")
    print("  - fptr1C.log       : Лог интеграции с 1С")

    print("\nУровни логирования:")
    print("  - ERROR : Только ошибки")
    print("  - INFO  : Базовое логирование")
    print("  - DEBUG : Расширенное логирование (включая протокол обмена)")

    print("\nКатегории логов:")
    print("  - FiscalPrinter          : Высокоуровневая работа с драйвером")
    print("  - Transport              : Обмен с ККТ")
    print("  - EthernetOverTransport  : Обмен ККТ с интернетом")
    print("  - DeviceDebug            : Отладочный вывод ККТ")
    print("  - USB, COM, TCP, Bluetooth : Низкоуровневые каналы обмена")

    print("\n" + "=" * 60)
    print("Примеры завершены!")
    print("Проверьте созданные файлы конфигурации и логов.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
