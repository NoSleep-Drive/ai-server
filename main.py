from pathlib import Path
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
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
from utils.exception_handlers import validation_exception_handler, http_exception_handler, generic_exception_handler

from model_loader import load_model

logger = get_logger(__name__)
app = FastAPI()
app.add_middleware(BaseHTTPMiddleware, dispatch=log_request)

app.include_router(frame_router, tags=["진단용 이미지 저장"])
app.include_router(diagnosis_router, tags=["진단 결과 조회"])

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

async def load_model_async():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        model = await loop.run_in_executor(pool, load_model)
    return model

@app.on_event("startup")
async def startup_event():
    app.state.model = await load_model_async()

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
