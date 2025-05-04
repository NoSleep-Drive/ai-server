from pydantic import BaseModel

class FrameRequest(BaseModel):
    deviceUid: str
    frameIdx: int
    driverFrame: str
