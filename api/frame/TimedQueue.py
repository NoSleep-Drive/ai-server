from collections import deque
from datetime import datetime
from typing import Tuple, Deque
import asyncio
from PIL import Image

class TimedQueue:
    def __init__(self, maxsize=48, window_seconds=2):
        self.maxsize = maxsize
        self.window_seconds = window_seconds
        self._items: Deque[Tuple[int, Image.Image, datetime]] = deque()
        self._condition = asyncio.Condition()

    def _purge_expired(self, now: datetime):
        while self._items and (now - self._items[0][2]).total_seconds() >= self.window_seconds:
            self._items.popleft()

    async def put(self, item: Tuple[int, Image.Image]):
        now = datetime.utcnow()
        async with self._condition:
            # self._purge_expired(now)

            if len(self._items) >= self.maxsize:
                raise asyncio.QueueFull("TimedQueue full 상황")

            self._items.append((item[0], item[1], now))
            self._condition.notify()

    async def get_one(self) -> Tuple[int, Image.Image]:
        async with self._condition:
            while True:
                now = datetime.utcnow()
                # self._purge_expired(now)

                if self._items:
                    frame_idx, image, _ = self._items.popleft()
                    return frame_idx, image

                await self._condition.wait()

    async def get_all(self) -> list[Tuple[int, Image.Image]]:
        async with self._condition:
            now = datetime.utcnow()
            # self._purge_expired(now)

            return [(idx, img) for idx, img, _ in self._items]

    def qsize(self) -> int:
        now = datetime.utcnow()
        # self._purge_expired(now)
        return len(self._items)
