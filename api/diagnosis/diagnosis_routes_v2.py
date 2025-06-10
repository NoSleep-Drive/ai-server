from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from utils.helper import create_error_response, get_logger
from utils.exception_handlers import ErrorForm
from api.frame.TimedQueue import TimedQueue
from api.frame.frame_routes import uid_queues, get_or_create_queue

router = APIRouter()
logger = get_logger(__name__)

@router.get("/diagnosis/drowsiness/v2")
async def get_diagnosis_result_v2(request: Request, device_uid: str = Query(..., alias="deviceUid")):
    model = request.app.state.model

    if model is None:
        logger.error("error_code:500, model_not_loaded, get_diagnosis_result(모델 로드 확인), 모델이 로드되지 않음")
        return create_error_response(500, "model_not_loaded", "get_diagnosis_result(모델 로드 확인)", "모델이 로드되지 않음")

    try:
        frames = await get_frames_from_queue(device_uid)

        input_array = preprocess_input_image(frames)
    except ErrorForm as e:
        logger.error(f"error_code:{e.code}, {e.message}, get_diagnosis_result(큐에서 이미지 가져올 때), {e.detail_message}")
        return create_error_response(e.code, e.message, "get_diagnosis_result(큐에서 이미지 가져올 때)", e.detail_message)

    try:
        is_drowsiness_drive = True
        for img in input_array:  # img.shape == (145, 145, 3)
            input_tensor = np.expand_dims(img, axis=0)  # shape == (1, 145, 145, 3)

            predicted_class  = model.predict(input_tensor)

            if predicted_class >= 0.00016:
                is_drowsiness_drive = False
                break

        detection_time = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        logger.error(f"error_code:500, prediction_error, get_diagnosis_result(모델 예측), {str(e)}")
        return create_error_response(500, "prediction_error", "get_diagnosis_result(모델 예측)", f"모델 예측 중 오류 발생: {str(e)}")


    logger.info(f"라즈베리 파이 UID: {device_uid} - 진단 결과: {is_drowsiness_drive}")
    return JSONResponse(
        status_code=200,
        content={
            "status": 200,
            "success": True,
            "isDrowsinessDrive": is_drowsiness_drive,
            "detectionTime": detection_time
        }
    )

async def get_frames_from_queue(device_uid: str):
    if device_uid not in uid_queues:
        raise ErrorForm(404, "queue_not_found", "해당 라즈베리 파이 UID에 대한 큐가 없습니다.")

    queue: TimedQueue = get_or_create_queue(device_uid)
    frames = await queue.get_all()

    if not frames:
        raise ErrorForm(404, "no_frames", "큐에 저장된 이미지 프레임이 없습니다.")

    if queue.qsize() < 6:
        raise ErrorForm(400, "insufficient_frames", "진단에 쓰일 이미지 프레임 수가 충분하지 않습니다.")

    frames.sort(key=lambda x: x[0])
    return [img for _, img in frames]

def preprocess_input_image(frames: list) -> np.ndarray:
    try:
        processed_images = []
        for frame in frames:
            image = np.array(frame)
            image = cv2.resize(image, (145, 145))
            image = image / 255.0
            processed_images.append(image)

        return np.array(processed_images)  # (N, 145, 145, 3)
    except (ValueError, cv2.error) as e:
        raise ErrorForm(422, "invalid_data", f"입력 이미지들을 numpy 배열로 변환 중 오류: {str(e)}") from e
