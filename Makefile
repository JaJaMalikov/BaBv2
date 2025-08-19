# Common developer tasks
.PHONY: run run-entry test lint fmt typecheck install-dev

run:
	python macronotron.py

run-entry:
	macronotron

test:
	pytest -q

lint:
	ruff check .
	black --check .

fmt:
	black .

typecheck:
	mypy core controllers ui macronotron.py

install-dev:
	pip install -r requirements.txt -r dev-requirements.txt
