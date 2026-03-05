from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class MediaItem(BaseModel):
    """Represents a single media attachment."""

    type: str = Field(..., description="Media type such as image, audio, file")
    url: HttpUrl


class NoteBase(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = ""
    tags: List[str] = Field(default_factory=list)
    owner_id: str = "anonymous"


class NoteCreate(NoteBase):
    media: List[MediaItem] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    media: Optional[List[MediaItem]] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None


class NoteOut(NoteBase):
    note_id: str
    media: List[MediaItem] = Field(default_factory=list)
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
