.PHONY: help install panel test lint format serve mlflow clean

help:
	@echo "Saudi Road Safety Analytics Platform"
	@echo ""
	@echo "Targets:"
	@echo "  install   Install Python dependencies"
	@echo "  panel     Build the regional data panel from raw GASTAT files"
	@echo "  test      Run unit tests"
	@echo "  lint      Run ruff linter"
	@echo "  format    Format code with ruff"
	@echo "  serve     Run FastAPI locally"
	@echo "  mlflow    Start MLflow tracking server at :5000"
	@echo "  clean     Remove generated files"

install:
	pip install -r requirements.txt

panel:
	python src/data/build_panel.py

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

serve:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

mlflow:
	mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf data/processed/*.csv
