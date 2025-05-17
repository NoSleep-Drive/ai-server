from pathlib import Path
import sys, os
module_path = Path(__file__).parent
sys.path.append(str(module_path))

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from api.frame.frame_routes import router as frame_router
from api.diagnosis.diagnosis_routes import router as diagnosis_router
from utils.helper import get_logger
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logging_middleware import log_request
from utils.exception_handlers import validation_exception_handler,http_exception_handler,generic_exception_handler

import tensorflow as tf

logger = get_logger(__name__)
app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=log_request)

app.include_router(frame_router, tags=["진단용 이미지 저장"])
app.include_router(diagnosis_router, tags=["진단 결과 조회"])

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

model = None


@app.on_event("startup")
def load_model():
    global model
    model_path = "./models/team12.h5"

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"해당 경로에서 모델을 찾을 수 없음 {model_path}")

    model = tf.keras.models.load_model(model_path)
    logger.info("모델 로드 성공")

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
