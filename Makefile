.DEFAULT_GOAL := check_code

format:
	isort --settings-file .isort.cfg .
	black --config pyproject.toml .

check_code:
	isort -c --diff --settings-file .isort.cfg .
	black --config pyproject.toml --check .
	pylint --rcfile=.pylintrc --errors-only financial
	mypy .
