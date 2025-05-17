from fastapi import APIRouter, Query, Request
from utils.helper import create_error_response, get_logger
from utils.exception_handlers import ErrorForm
from fastapi.responses import JSONResponse
from api.frame.TimedQueue import TimedQueue
from api.frame.frame_routes import uid_queues, get_or_create_queue

import cv2
import numpy as np
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

@router.get("/api/diagnosis/drowiness")
async def get_diagnosis_result(request: Request, device_uid: str = Query(..., alias="deviceUid")):
    model = request.app.state.model

    if model is None:
        logger.error("error_code:500, model_not_loaded, get_diagnosis_result(모델 로드 확인), 모델이 로드되지 않음")
        return create_error_response(500, "model_not_loaded", "get_diagnosis_result(모델 로드 확인)", "모델이 로드되지 않음")

    try:
        frames = await get_frames_from_queue(device_uid)
        if not frames:
            raise ErrorForm(404, "no_frames", "get_diagnosis_result(프레임 조회)")

        input_array = preprocess_input_data(frames)
    except ErrorForm as e:
        logger.error(f"error_code:{e.code}, {e.message}, get_diagnosis_result(입력 데이터 처리), {e.detail_message}")
        return create_error_response(e.code, e.message, "get_diagnosis_result(입력 데이터 처리)", e.detail_message)

    try:
        predicted_class  = model.predict(input_array)
        logger.info(f"모델 결과 반환 값(확률): {predicted_class}")

        predicted_class_int = (predicted_class.flatten()[0] > 0.5).astype(int)
        logger.info(f"모델 결과 반환 값 (이진): {predicted_class_int}")
    except Exception as e:
        logger.error(f"error_code:500, prediction_error, get_diagnosis_result(모델 예측), {str(e)}")
        return create_error_response(500, "prediction_error", "get_diagnosis_result(모델 예측)", f"모델 예측 중 오류 발생: {str(e)}")

    predicted_result = True if predicted_class_int == 0 else False
    detection_time = datetime.utcnow().isoformat() + "Z"
    logger.info(f"라즈베리 파이 UID: {device_uid} - 진단 결과: {predicted_result}")
    return JSONResponse(
        status_code=200,
        content={
            "status": 200,
            "success": True,
            "isDrowsinessDrive": predicted_result,
            "detectionTime": detection_time
        }
    )


async def get_frames_from_queue(device_uid: str):
    if device_uid not in uid_queues:
        raise ErrorForm(404, "queue_not_found", "get_frames_from_queue")

    queue: TimedQueue = get_or_create_queue(device_uid)
    frames = await queue.get_all()

    if not frames:
        raise ErrorForm(404, "no_frames", "get_frames_from_queue")

    frames.sort(key=lambda x: x[0])
    return [img for _, img in frames]


def preprocess_input_data(frames: list) -> np.ndarray:
    try:
        resized_frames = [cv2.resize(np.array(frame), (145, 145)) for frame in frames]

        frame_count = 48
        if len(resized_frames) < frame_count:
            padding_frames = [np.zeros((145, 145, 3))] * (frame_count - len(resized_frames))
            resized_frames.extend(padding_frames)
        else:
            resized_frames = resized_frames[:frame_count]

        image_array = [frame / 255.0 for frame in resized_frames]
        input_array = np.array(image_array)
        input_array = np.expand_dims(input_array, axis=0)  # (1, 48, 145, 145, 3)

        return input_array
    except Exception as e:
        raise ErrorForm(422, "invalid_data", f"입력 데이터를 numpy 배열로 변환 중 오류: {str(e)}")
