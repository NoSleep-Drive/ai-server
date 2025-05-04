import os, logging
from datetime import datetime
import logging.config
import contextvars

request_uuid = contextvars.ContextVar("request_uuid", default=None)

log_directory = "log"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

USE_INFO_LOG = True


class IgnoreInfoFilter(logging.Filter):
    def filter(self, record):
        return USE_INFO_LOG or record.levelno > logging.INFO


def get_log_filename(log_type: str) -> str:
    current_date = datetime.now().strftime("%Y%m%d")
    return os.path.join(log_directory, f"{log_type}.log_{current_date}")


class UUIDFormatter(logging.Formatter):
    def format(self, record):
        record.request_uuid = get_request_uuid()
        return super().format(record)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - [%(request_uuid)s] - %(name)s - %(levelname)s - %(message)s",
            "()": UUIDFormatter,
        },
    },
    "filters": {
        "info_filter": {  # info_filter 필터 등록
            "()": IgnoreInfoFilter,
        },
    },
    "handlers": {
        "file_warning": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": get_log_filename("warning"),
            "level": "WARNING",
            "encoding": "utf-8",
        },
        "file_info": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": get_log_filename("info"),
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["info_filter"] if not USE_INFO_LOG else [],
        },
        "file_middleware": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": get_log_filename("middleware"),
            "level": "INFO",
            "encoding": "utf-8",
        },
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
        }
    },
}

# 로깅 설정 적용
logging.config.dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def get_middleware_logger() -> logging.Logger:
    return logging.getLogger("middleware_logger")


def create_error_response(code, message, method, detail_message):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "method": method,
            "detail_message": detail_message
        }
    }


def set_request_uuid(uuid: str):
    request_uuid.set(uuid)


def get_request_uuid():
    return request_uuid.get()
