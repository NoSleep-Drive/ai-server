import os, logging
from datetime import datetime
import logging.config
import contextvars
from fastapi.responses import JSONResponse

request_uuid = contextvars.ContextVar("request_uuid", default=None)

LOG_DIRECTORY = "log"
os.makedirs(LOG_DIRECTORY, exist_ok=True)

USE_INFO_LOG = True


class IgnoreInfoFilter(logging.Filter):
    def filter(self, record):
        return USE_INFO_LOG or record.levelno > logging.INFO


def get_log_filename(log_type: str) -> str:
    current_date = datetime.now().strftime("%Y%m%d")
    return os.path.join(LOG_DIRECTORY, f"{log_type}.log_{current_date}")


class UUIDFormatter(logging.Formatter):
    def format(self, record):
        record.request_uuid = get_request_uuid()
        return super().format(record)


def file_handler_factory(log_type: str, level: str, filters=None) -> dict:
    return {
        "class": "logging.FileHandler",
        "formatter": "default",
        "filename": get_log_filename(log_type),
        "level": level,
        "encoding": "utf-8",
        "filters": filters or [],
    }

def init_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - [%(request_uuid)s] - %(name)s - %(levelname)s - %(message)s",
                "()": UUIDFormatter,
            },
        },
        "filters": {
            "info_filter": {
                "()": IgnoreInfoFilter,
            },
        },
        "handlers": {
            "file_warning": file_handler_factory("warning", "WARNING"),
            "file_info": file_handler_factory(
                "info", "INFO", filters=["info_filter"] if not USE_INFO_LOG else []
            ),
            "file_middleware": file_handler_factory("middleware", "INFO"),
        },
        "loggers": {
            "": {
                "handlers": ["file_warning"] + (["file_info"] if USE_INFO_LOG else []),
                "level": "DEBUG",
            },
            "httpx": {
                "handlers": ["file_warning"],
                "level": "WARNING",
                "propagate": False,
            },
            "middleware_logger": {
                "handlers": ["file_middleware"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def get_middleware_logger() -> logging.Logger:
    return logging.getLogger("middleware_logger")


def create_error_response(code, message, method, detail_message):
    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "method": method,
                "detail_message": detail_message
            }
        }
    )


def set_request_uuid(uuid: str):
    request_uuid.set(uuid)


def get_request_uuid():
    return request_uuid.get()

init_logging()
