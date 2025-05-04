from pydantic import BaseModel

class FrameRequest(BaseModel):
    deviceUid: str
    frameIdx: str
    driverFrame: str
