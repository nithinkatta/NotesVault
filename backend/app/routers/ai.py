from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.config import Settings, get_settings
from app.db.mongo import get_collection
from app.db.repository import NoteRepository
from app.schemas.ai import OCRRequest, SummarizeRequest, TranscribeRequest
from app.schemas.note import NoteUpdate
from app.services.ai import perform_ocr, summarize_text, transcribe_audio

router = APIRouter()


def get_repo(collection: AsyncIOMotorCollection = Depends(get_collection)) -> NoteRepository:
    return NoteRepository(collection)


@router.post("/summarize")
async def summarize(
    payload: SummarizeRequest,
    settings: Settings = Depends(get_settings),
    repo: NoteRepository = Depends(get_repo),
) -> dict:
    result = await summarize_text(settings, payload.content)
    summary = result.get("summary", "")
    keywords = result.get("keywords") or []

    if payload.note_id:
        updated = await repo.update_note(
            payload.note_id, NoteUpdate(summary=summary, keywords=keywords)
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return {"summary": summary, "keywords": keywords}


@router.post("/ocr")
async def ocr(
    payload: OCRRequest,
    settings: Settings = Depends(get_settings),
    repo: NoteRepository = Depends(get_repo),
) -> dict:
    text = await perform_ocr(settings, payload.image_url)

    if payload.note_id:
        existing = await repo.get_note(payload.note_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        new_content = f"{existing.content}\n\n[OCR]\n{text}" if existing.content else text
        await repo.update_note(payload.note_id, NoteUpdate(content=new_content))

    return {"text": text}


@router.post("/transcribe")
async def transcribe(
    payload: TranscribeRequest,
    settings: Settings = Depends(get_settings),
    repo: NoteRepository = Depends(get_repo),
) -> dict:
    text = await transcribe_audio(settings, payload.audio_url)

    if payload.note_id:
        existing = await repo.get_note(payload.note_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
        new_content = (
            f"{existing.content}\n\n[Transcription]\n{text}" if existing.content else text
        )
        await repo.update_note(payload.note_id, NoteUpdate(content=new_content))

    return {"text": text}
