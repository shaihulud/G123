#!/bin/bash
set -e

PORT=${2:-8000}

case "$1" in
    start)
        alembic upgrade head
        uvicorn financial.main:app --host 0.0.0.0 --port $PORT --reload
        ;;
    linters)
        isort -c --diff --settings-file .isort.cfg .
        black --config pyproject.toml --check .
        pylint --rcfile=.pylintrc --errors-only financial
        mypy .
        exit 0
        ;;
    get-raw-data)
        alembic upgrade head
        python get_raw_data.py
        ;;
    pytest)
        alembic downgrade base
        alembic upgrade head
        pytest -s -vv -x tests/ --trace-config
        exit 0
        ;;
    *)
        exec "$@"
        ;;
esac
