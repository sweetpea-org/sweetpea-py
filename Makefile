.PHONY: all full typecheck test acceptance

all: typecheck test
full: typecheck test acceptance

typecheck:
	@echo "Typechecking..."
	mypy --ignore-missing-imports sweetpea

test: typecheck test-no-typecheck

test-no-typecheck:
	@echo "Running tests..."
	env SWEETPEA_CHECK_SYNTHESIZED=y python3 -m pytest -vv -p no:warnings sweetpea

acceptance:
	@echo "Running acceptance tests..."
	env SWEETPEA_CHECK_SYNTHESIZED=y python3 -m pytest -p no:warnings acceptance

acceptance-slow:
	@echo "Running acceptance tests, including tests marked as slow..."
	env SWEETPEA_CHECK_SYNTHESIZED=y python3 -m pytest -p no:warnings acceptance --run-slow
