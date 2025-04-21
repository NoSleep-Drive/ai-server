from pydantic import BaseModel

class FrameRequest(BaseModel):
    deviceUid: str
    driverFrame: str
