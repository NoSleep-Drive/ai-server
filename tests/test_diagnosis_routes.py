import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from main import app
from api.frame.frame_routes import uid_queues
from api.frame.TimedQueue import TimedQueue
import numpy as np
from PIL import Image


@pytest.mark.asyncio
async def test_get_diagnosis_success():
    device_uid = "uid_success"
    queue = TimedQueue(maxsize=48, window_seconds=2)

    for i in range(48):
        img = Image.new("RGB", (145, 145), color="blue") # 임의 이미지 데이터 세팅
        await queue.put((i, img))
    uid_queues[device_uid] = queue

    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.3]])

    app.state.model = mock_model

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/ai/diagnosis/drowsiness", params={"deviceUid": device_uid})

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["isDrowsinessDrive"] is True # 0.5 이하는 True 반환
    assert "detectionTime" in data

@pytest.mark.asyncio
async def test_model_not_loaded():
    app.state.model = None
    device_uid = "uid_any"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/ai/diagnosis/drowsiness", params={"deviceUid": device_uid})

    assert resp.status_code == 500
    data = resp.json()
    assert data["error"]["message"] == "model_not_loaded"

@pytest.mark.asyncio
async def test_queue_not_found():
    app.state.model = MagicMock()
    device_uid = "nonexistent_uid"

    if device_uid in uid_queues:
        del uid_queues[device_uid]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/ai/diagnosis/drowsiness", params={"deviceUid": device_uid})

    assert resp.status_code == 404
    assert resp.json()["error"]["message"] == "queue_not_found"
