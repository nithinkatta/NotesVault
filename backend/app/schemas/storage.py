from pydantic import BaseModel, Field


class PresignRequest(BaseModel):
    file_name: str = Field(..., description="Original file name")
    content_type: str = Field(
        default="application/octet-stream", description="MIME type of the upload"
    )
    note_id: str | None = Field(
        default=None, description="Optional note id to namespace the upload"
    )


class PresignResponse(BaseModel):
    upload_url: str
    object_url: str
    expires_in: int
    key: str
