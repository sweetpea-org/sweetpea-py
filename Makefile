.PHONY: all full typecheck test acceptance

all: typecheck test
full: typecheck test acceptance

typecheck:
	@echo "Typechecking..."
	mypy --ignore-missing-imports sweetpea

test: typecheck
	@echo "Running tests..."
	python3 -m pytest -vv -p no:warnings sweetpea

acceptance:
	@echo "Running acceptance tests..."
	python3 -m pytest -vv -p no:warnings acceptance
