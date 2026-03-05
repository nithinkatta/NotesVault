from pydantic import BaseModel, HttpUrl


class SummarizeRequest(BaseModel):
    content: str
    note_id: str | None = None


class OCRRequest(BaseModel):
    image_url: HttpUrl
    note_id: str | None = None


class TranscribeRequest(BaseModel):
    audio_url: HttpUrl
    note_id: str | None = None
