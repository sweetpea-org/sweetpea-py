.PHONY: all typecheck test

all: typecheck test

typecheck:
	@echo "Typechecking..."
	mypy --ignore-missing-imports FrontEnd.py tests.py

test: typecheck
	@echo "Running tests..."
	pytest -vv tests.py
