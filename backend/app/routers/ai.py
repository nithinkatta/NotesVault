from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.db.dynamo import NotesRepository
from app.db.local_repo import LocalNotesRepository
from app.schemas.ai import OCRRequest, SummarizeRequest, TranscribeRequest
from app.schemas.note import NoteUpdate
from app.services.ai import perform_ocr, summarize_text, transcribe_audio

router = APIRouter()


def get_repo(settings: Settings = Depends(get_settings)):
    if settings.use_local_store:
        return LocalNotesRepository(settings)
    return NotesRepository(settings)


@router.post("/summarize")
async def summarize(
    payload: SummarizeRequest,
    settings: Settings = Depends(get_settings),
    repo: NotesRepository = Depends(get_repo),
) -> dict:
    result = await summarize_text(settings, payload.content)
    summary = result.get("summary", "")
    keywords = result.get("keywords") or []

    if payload.note_id:
        updated = repo.update_note(
            payload.note_id, NoteUpdate(summary=summary, keywords=keywords)
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return {"summary": summary, "keywords": keywords}


@router.post("/ocr")
async def ocr(
    payload: OCRRequest,
    settings: Settings = Depends(get_settings),
    repo: NotesRepository = Depends(get_repo),
) -> dict:
    text = await perform_ocr(settings, payload.image_url)

    if payload.note_id:
        existing = repo.get_note(payload.note_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        new_content = f"{existing.content}\n\n[OCR]\n{text}" if existing.content else text
        repo.update_note(payload.note_id, NoteUpdate(content=new_content))

    return {"text": text}


@router.post("/transcribe")
async def transcribe(
    payload: TranscribeRequest,
    settings: Settings = Depends(get_settings),
    repo: NotesRepository = Depends(get_repo),
) -> dict:
    text = await transcribe_audio(settings, payload.audio_url)

    if payload.note_id:
        existing = repo.get_note(payload.note_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        new_content = (
            f"{existing.content}\n\n[Transcription]\n{text}" if existing.content else text
        )
        repo.update_note(payload.note_id, NoteUpdate(content=new_content))

    return {"text": text}
