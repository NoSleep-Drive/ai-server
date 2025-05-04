import asyncio
from datetime import datetime
from PIL import Image
from typing import Tuple

class TimedQueue:
    def __init__(self, maxsize=48, window_seconds=2):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.window_seconds = window_seconds

    async def _remove_expired(self):
        now = datetime.utcnow()
        items = []

        while not self.queue.empty():
            item = await self.queue.get()
            frame_idx, image, timestamp = item
            if (now - timestamp).total_seconds() < self.window_seconds:
                items.append(item)

        for item in items:
            await self.queue.put(item)

    async def put(self, item: Tuple[str, Image.Image]):
        await self._remove_expired()
        timestamped_item = (item[0], item[1], datetime.utcnow())
        await self.queue.put(timestamped_item)

    async def get(self) -> Tuple[str, Image.Image]:
        frame_idx, image, _ = await self.queue.get()
        return frame_idx, image
