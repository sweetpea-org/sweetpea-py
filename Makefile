.PHONY: all typecheck test

all: typecheck test

typecheck:
	@echo "Typechecking..."
	mypy --ignore-missing-imports sweetpea

test: typecheck
	@echo "Running tests..."
	python3 -m pytest -vv
