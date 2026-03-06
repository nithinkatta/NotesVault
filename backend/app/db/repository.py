from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument

from app.schemas.note import NoteCreate, NoteOut, NoteUpdate


class NoteRepository:
    """MongoDB-backed CRUD for notes."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self.collection = collection

    async def create_note(self, payload: NoteCreate) -> NoteOut:
        now = datetime.now(timezone.utc)
        note_id = str(uuid4())
        doc = {
            "note_id": note_id,
            "title": payload.title,
            "content": payload.content,
            "tags": payload.tags,
            "owner_id": payload.owner_id,
            "media": [m.model_dump() for m in payload.media],
            "summary": None,
            "keywords": [],
            "created_at": now,
            "updated_at": now,
        }
        await self.collection.insert_one(doc)
        return self._to_schema(doc)

    async def get_note(self, note_id: str) -> NoteOut | None:
        doc = await self.collection.find_one({"note_id": note_id})
        if not doc:
            return None
        return self._to_schema(doc)

    async def list_notes(self) -> List[NoteOut]:
        cursor = self.collection.find().sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [self._to_schema(doc) for doc in docs]

    async def update_note(self, note_id: str, payload: NoteUpdate) -> NoteOut | None:
        updates = {}
        if payload.title is not None:
            updates["title"] = payload.title
        if payload.content is not None:
            updates["content"] = payload.content
        if payload.tags is not None:
            updates["tags"] = payload.tags
        if payload.media is not None:
            updates["media"] = [m.model_dump() for m in payload.media]
        if payload.summary is not None:
            updates["summary"] = payload.summary
        if payload.keywords is not None:
            updates["keywords"] = payload.keywords

        if not updates:
            existing = await self.get_note(note_id)
            return existing

        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"note_id": note_id},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None
        return self._to_schema(result)

    async def delete_note(self, note_id: str) -> bool:
        res = await self.collection.delete_one({"note_id": note_id})
        return res.deleted_count == 1

    @staticmethod
    def _to_schema(doc: dict) -> NoteOut:
        return NoteOut(
            note_id=doc["note_id"],
            title=doc.get("title", ""),
            content=doc.get("content", ""),
            tags=doc.get("tags", []),
            owner_id=doc.get("owner_id", "anonymous"),
            media=doc.get("media", []),
            summary=doc.get("summary"),
            keywords=doc.get("keywords", []),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
        )
