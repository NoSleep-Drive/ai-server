from fastapi import APIRouter
from .frame_models import FrameRequest
from utils.helper import create_error_response, get_logger
from utils.exception_handlers import ErrorForm
from fastapi.responses import JSONResponse
from .TimedQueue import TimedQueue

import aiohttp
import asyncio
import base64
import queue
from typing import Dict, Tuple
from PIL import Image
from io import BytesIO
router = APIRouter()
logger = get_logger(__name__)

uid_queues: Dict[str, TimedQueue] = {}


@router.post("/api/save/frame")
async def save_frame(data: FrameRequest):
    device_uid = data.deviceUid
    frame_idx = data.frameIdx
    frame_data = data.driverFrame

    try:
        image = decode_base64_image(frame_data)
    except ErrorForm as e:
        return create_error_response(e.code, e.message, "save_frame", e.detail_message)

    if device_uid not in uid_queues:
        uid_queues[device_uid] = TimedQueue(maxsize=48, window_seconds=2)

    try:
        await uid_queues[device_uid].put((frame_idx, image))
        return JSONResponse(status_code=200, content={"status": 200, "success": True})
    except queue.Full:
        return create_error_response(429, "queue_full", "save_frame", f"해당 라즈베리 파이 기준 큐 사이즈 초과: {device_uid}")
    except Exception as e:
        return create_error_response(500, "queue_error", "save_frame", f"큐에 이미지 저장 실패: {str(e)}")


def decode_base64_image(base64_str: str) -> Image.Image:
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        image_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(image_data))
        return image
    except base64.binascii.Error as e:
        raise ErrorForm(422, "invalid_base64", f"Base64 디코딩 실패: {str(e)}")
    except Exception as e:
        raise ErrorForm(422, "invalid_image", f"이미지 디코딩 중 오류: {str(e)}")
