from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.helper import get_logger, create_error_response

logger = get_logger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for request: {request.url} - {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "422",
                "message": "invalid_parameter",
                "method": request.method.lower(),
                "detail_message": "제공된 파라미터가 잘못되었거나 필수 필드가 누락되었습니다.",
                "details": exc.errors()
            },
        },
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_responses = {
        400: ("H00001", "400_bad_request", "잘못된 요청입니다."),
        401: ("H00002", "401_unauthorized", "액세스 권한이 없습니다."),
        404: ("H00003", "404_not_found", "요청하신 리소스를 찾을 수 없습니다."),
        422: ("H00004", "422_invalid_parameter", "처리할 수 없는 엔티티 존재합니다."),
        429: ("H00005", "429_too_many_request", "요청이 너무 많습니다."),
        500: ("H00006", "500_internal_server", "서버 내부 오류가 발생했습니다.")
    }

    error_code, error_message, description = error_responses.get(
        exc.status_code,
        (f"H{exc.status_code:05}", exc.detail, "HTTP 예외가 발생했습니다.")
    )

    logger.error(f"{exc.status_code} error for request: {request.url} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": str(exc.status_code),
                "message": error_message,
                "method": request.method.lower(),
                "detail_message": description
            },
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error for request: {request.url} - {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "500",
                "message": "internal_server_error",
                "method": request.method.lower(),
                "detail_message": "서버 내부 오류가 발생했습니다. 관리자에게 문의하세요.",
            },
        },
    )

class ErrorForm(Exception):
    """커스텀 에러 폼"""
    def __init__(self, code, message, detail_message):
        self.code = code
        self.message = message
        self.detail_message = detail_message
        super().__init__(self.message)
