from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from uuid import uuid4

from app.config import Settings
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate


class LocalNotesRepository:
    """File-backed notes repository for local/dev without AWS."""

    def __init__(self, settings: Settings) -> None:
        self.data_path = Path(settings.data_dir)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_path / "notes.json"
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _read_all(self) -> list[dict]:
        try:
            raw = self.file_path.read_text(encoding="utf-8")
            return json.loads(raw)
        except Exception:
            return []

    def _write_all(self, items: list[dict]) -> None:
        self.file_path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def create_note(self, payload: NoteCreate) -> NoteOut:
        now = datetime.now(timezone.utc).isoformat()
        note_id = str(uuid4())
        item = {
            "note_id": note_id,
            "title": payload.title,
            "content": payload.content,
            "tags": payload.tags,
            "owner_id": payload.owner_id,
            "media": [media.model_dump() for media in payload.media],
            "summary": None,
            "keywords": [],
            "created_at": now,
            "updated_at": now,
        }
        items = self._read_all()
        items.append(item)
        self._write_all(items)
        return self._deserialize(item)

    def get_note(self, note_id: str) -> NoteOut | None:
        for item in self._read_all():
            if item["note_id"] == note_id:
                return self._deserialize(item)
        return None

    def list_notes(self) -> List[NoteOut]:
        return [self._deserialize(item) for item in self._read_all()]

    def update_note(self, note_id: str, payload: NoteUpdate) -> NoteOut | None:
        items = self._read_all()
        updated_item = None
        for idx, item in enumerate(items):
            if item["note_id"] != note_id:
                continue
            updated = item.copy()
            if payload.title is not None:
                updated["title"] = payload.title
            if payload.content is not None:
                updated["content"] = payload.content
            if payload.tags is not None:
                updated["tags"] = payload.tags
            if payload.media is not None:
                updated["media"] = [m.model_dump() for m in payload.media]
            if payload.summary is not None:
                updated["summary"] = payload.summary
            if payload.keywords is not None:
                updated["keywords"] = payload.keywords
            updated["updated_at"] = datetime.now(timezone.utc).isoformat()
            items[idx] = updated
            updated_item = updated
            break
        if updated_item is None:
            return None
        self._write_all(items)
        return self._deserialize(updated_item)

    def delete_note(self, note_id: str) -> bool:
        items = self._read_all()
        new_items = [i for i in items if i["note_id"] != note_id]
        if len(new_items) == len(items):
            return False
        self._write_all(new_items)
        return True

    @staticmethod
    def _deserialize(item: dict) -> NoteOut:
        return NoteOut(
            note_id=item["note_id"],
            title=item.get("title", ""),
            content=item.get("content", ""),
            tags=item.get("tags", []),
            owner_id=item.get("owner_id", "anonymous"),
            media=item.get("media", []),
            summary=item.get("summary"),
            keywords=item.get("keywords", []),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )
