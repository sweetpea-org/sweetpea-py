.PHONY: all typecheck test backend

all: typecheck test backend

typecheck:
	@echo "Typechecking..."
	mypy FrontEnd.py tests.py

test: typecheck
	@echo "Running tests..."
	pytest -vv tests.py

backend:
	@echo "Building backend..."
	cd sweetpea-core && stack build && cd -
