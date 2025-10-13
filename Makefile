.PHONY: install test format lint clean run-example run-advanced run-server run-server-dev help

help:
	@echo "Доступные команды:"
	@echo "  make install       - Установить зависимости"
	@echo "  make install-dev   - Установить зависимости для разработки"
	@echo "  make run-server    - Запустить REST API сервер"
	@echo "  make run-server-dev - Запустить сервер с auto-reload"
	@echo "  make test          - Запустить тесты"
	@echo "  make test-cov      - Запустить тесты с покрытием"
	@echo "  make format        - Форматировать код с помощью black"
	@echo "  make lint          - Проверить код с помощью flake8 и mypy"
	@echo "  make clean         - Очистить временные файлы"
	@echo "  make run-example   - Запустить базовый пример драйвера"
	@echo "  make run-advanced  - Запустить расширенные примеры драйвера"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e .
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest --cov=atol_integration --cov-report=html --cov-report=term

format:
	black atol_integration/ tests/ examples/

lint:
	flake8 atol_integration/ tests/ examples/ --max-line-length=120
	mypy atol_integration/ --ignore-missing-imports

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

run-example:
	python examples/driver_basic_usage.py

run-advanced:
	python examples/driver_advanced_usage.py

run-server:
	python -m uvicorn atol_integration.api.server:app --host 0.0.0.0 --port 8000

run-server-dev:
	python -m uvicorn atol_integration.api.server:app --host 0.0.0.0 --port 8000 --reload
