.PHONY: all typecheck test

all: typecheck test

typecheck:
	@echo "Typechecking..."
	mypy FrontEnd.py tests.py

test: typecheck
	@echo "Running tests..."
	pytest -vv tests.py
