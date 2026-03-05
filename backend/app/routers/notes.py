from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.db.dynamo import NotesRepository
from app.db.local_repo import LocalNotesRepository
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.schemas.storage import PresignRequest, PresignResponse
from app.services.storage import create_presigned_upload

router = APIRouter()


def get_repo(settings: Settings = Depends(get_settings)):
    if settings.use_local_store:
        return LocalNotesRepository(settings)
    return NotesRepository(settings)


def get_settings_dep(settings: Settings = Depends(get_settings)) -> Settings:
    return settings


@router.get("/", response_model=list[NoteOut])
def list_notes(repo: NotesRepository = Depends(get_repo)) -> list[NoteOut]:
    return repo.list_notes()


@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, repo=Depends(get_repo)) -> NoteOut:
    return repo.create_note(payload)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: str, repo=Depends(get_repo)) -> NoteOut:
    note = repo.get_note(note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: str,
    payload: NoteUpdate,
    repo=Depends(get_repo),
) -> NoteOut:
    note = repo.update_note(note_id, payload)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str, repo=Depends(get_repo)) -> None:
    existing = repo.get_note(note_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    repo.delete_note(note_id)
    return None


@router.post("/presign", response_model=PresignResponse)
def presign_upload(
    payload: PresignRequest,
    settings: Settings = Depends(get_settings_dep),
) -> PresignResponse:
    result = create_presigned_upload(
        settings=settings,
        file_name=payload.file_name,
        content_type=payload.content_type,
        note_id=payload.note_id,
    )
    return PresignResponse(
        upload_url=result.upload_url,
        object_url=result.object_url,
        expires_in=result.expires_in,
        key=result.key,
    )


@router.put("/upload/{key:path}", status_code=status.HTTP_201_CREATED)
async def upload_file(
    key: str,
    request: Request,
    settings: Settings = Depends(get_settings_dep),
):
    """
    Local upload sink used when use_local_store=True.
    """
    if not settings.use_local_store:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Local upload disabled"
        )

    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = await request.body()
    dest.write_bytes(body)
    return {"object_url": f"{settings.api_base_url}/static/{key}"}
