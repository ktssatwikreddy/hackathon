from datetime import datetime

from pydantic import BaseModel


class QrTokenOut(BaseModel):
    token: str
    checkin_url: str
    qr_png_base64: str
    expires_at: datetime
    session_id: int


class CheckinRequest(BaseModel):
    token: str


class CheckinResponse(BaseModel):
    status: str
    session_id: int
    training_title: str
    already_marked: bool
