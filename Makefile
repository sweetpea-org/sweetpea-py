.PHONY: all typecheck test

all: typecheck test

typecheck:
	@echo "Typechecking..."
	mypy --ignore-missing-imports sweetpea/__init__.py sweetpea/tests/test_sweetpea.py

test: typecheck
	@echo "Running tests..."
	python3 -m pytest -vv
