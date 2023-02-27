from logging import config
from typing import Any, Dict

from financial.config import settings


def make_logging_config() -> dict:
    level = "DEBUG" if settings.DEBUG else settings.LOG_LEVEL

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s %(levelname)s %(message)s",
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            },
        },
        "handlers": {
            "console": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "level": level,
            },
            "app": {
                "handlers": ["console"],
            },
            "uvicorn": {
                "handlers": ["console"],
            },
        },
    }
    return logging_config


def configure_logging():
    logging_config = make_logging_config()
    config.dictConfig(logging_config)
