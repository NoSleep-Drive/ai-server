import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from main import app
import base64
from PIL import Image
from io import BytesIO
from api.frame.frame_routes import uid_queues, get_or_create_queue, decode_base64_image


@pytest.mark.asyncio
async def test_save_frame_success_and_check_queue(): # 200 테스트
    device_uid = "test_device"
    img_str = create_test_image_base64()

    payload = {
        "deviceUid": device_uid,
        "frameIdx": 1,
        "driverFrame": f"data:image/jpeg;base64,{img_str}"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/save/frame", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True

    queue = uid_queues.get(device_uid)
    assert queue is not None
    assert queue.qsize() == 1

@pytest.mark.asyncio
async def test_invalid_base64_raises_custom_error(): # base64가 아닐 경우 테스트
    payload = {
        "deviceUid": "test_device_invalid",
        "frameIdx": 2,
        "driverFrame": "it-is-not-base64-encoding-form"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/save/frame", json=payload)

    assert response.status_code == 422
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error"]["message"] == "invalid_base64"
    assert "Base64 디코딩 실패" in json_resp["error"]["detail_message"]

@pytest.mark.asyncio
async def test_invalid_image_raises_custom_error(): # 유효한 base64지만 이미지 포맷 아닌 경우 테스트
    dummy_data = base64.b64encode(b"it is not an image").decode("utf-8")

    payload = {
        "deviceUid": "test_device_invalid_img",
        "frameIdx": 3,
        "driverFrame": f"data:image/jpeg;base64,{dummy_data}"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/save/frame", json=payload)

    assert response.status_code == 422
    json_resp = response.json()
    assert json_resp["success"] is False
    assert json_resp["error"]["message"] == "invalid_image"
    assert "이미지 디코딩 중 오류" in json_resp["error"]["detail_message"]

@pytest.mark.asyncio
async def test_queue_full_raises_custom_error(monkeypatch): # 강제로 큐를 가득 채운 뒤 max 임계값 테스트
    device_uid = "dev_full_queue"
    image_b64 = create_test_image_base64()
    payload = {
        "deviceUid": device_uid,
        "frameIdx": 0,
        "driverFrame": f"data:image/jpeg;base64,{image_b64}"
    }

    queue = uid_queues.get(device_uid)
    if queue is None:
        queue = get_or_create_queue(device_uid)

    for i in range(queue.maxsize):
        await queue.put((i, decode_base64_image(image_b64)))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/save/frame", json=payload)

    json_resp = resp.json()
    assert resp.status_code == 429
    assert json_resp["error"]["message"] == "queue_full"
    assert json_resp["error"]["method"] == "save_frame(큐 저장)"

def create_test_image_base64():
    image = Image.new("RGB", (100, 100), color="red")
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")
