from pydantic import BaseModel

class DiagnosisRequest(BaseModel):
    deviceUid: str
