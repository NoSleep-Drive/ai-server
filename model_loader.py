import os
import tensorflow as tf
from utils.helper import get_logger

logger = get_logger(__name__)

def load_model(model_path: str = "./models/team12.h5"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"해당 경로에서 모델을 찾을 수 없음 {model_path}")

    model = tf.keras.models.load_model(model_path)
    logger.info("모델 로드 성공")
    return model
