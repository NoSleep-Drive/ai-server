import asyncio
from datetime import datetime
from PIL import Image
from typing import Tuple, List

class TimedQueue:
    def __init__(self, maxsize=48, window_seconds=2, clean_interval=1):
        self.maxsize = maxsize
        self.window_seconds = window_seconds
        self.clean_interval = clean_interval
        self._items: List[Tuple[int, Image.Image, datetime]] = []
        self._lock = asyncio.Lock()
        self._cleaner_task = asyncio.create_task(self._clean_expired_items())

    async def _clean_expired_items(self):
        while True:
            await asyncio.sleep(self.clean_interval)
            async with self._lock:
                now = datetime.utcnow()
                self._items = [
                    item for item in self._items
                    if (now - item[2]).total_seconds() < self.window_seconds
                ]

    async def put(self, item: Tuple[int, Image.Image]):
        async with self._lock:
            if len(self._items) >= self.maxsize:
                raise asyncio.QueueFull("TimedQueue full 상황")
            timestamped_item = (item[0], item[1], datetime.utcnow())
            self._items.append(timestamped_item)

    async def get(self) -> Tuple[int, Image.Image]:
        while True:
            async with self._lock:
                now = datetime.utcnow()
                self._items = [
                    item for item in self._items
                    if (now - item[2]).total_seconds() < self.window_seconds
                ]
                if self._items:
                    item = self._items.pop(0)
                    return item[0], item[1]
            await asyncio.sleep(0.1)

    def qsize(self) -> int:
        return len(self._items)
