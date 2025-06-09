import os
import tensorflow as tf
from utils.helper import get_logger

logger = get_logger(__name__)

class CastLayer(tf.keras.layers.Layer):
    def __init__(self, dtype=tf.float32, **kwargs):
        super().__init__(**kwargs)
        self.target_dtype = dtype

    def call(self, inputs):
        return tf.cast(inputs, self.target_dtype)

    def get_config(self):
        config = super().get_config()
        config.update({"dtype": self.target_dtype})
        return config

def load_model(model_path: str = "./models/team12-correction.h5"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"해당 경로에서 모델을 찾을 수 없음 {model_path}")

    model = tf.keras.models.load_model(
        model_path,
        custom_objects={"Cast": CastLayer}
    )
    logger.info("모델 로드 성공")
    return model
