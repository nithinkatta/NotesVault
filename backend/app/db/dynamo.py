from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import List
from uuid import uuid4

import boto3

from app.config import Settings
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate


@lru_cache
def _table(region: str, table_name: str):
    """Return a cached DynamoDB table handle."""
    resource = boto3.resource("dynamodb", region_name=region)
    return resource.Table(table_name)


class NotesRepository:
    """CRUD operations for notes backed by DynamoDB."""

    def __init__(self, settings: Settings) -> None:
        self.table = _table(settings.aws_region, settings.dynamo_table)

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
        self.table.put_item(Item=item)
        return self._deserialize(item)

    def get_note(self, note_id: str) -> NoteOut | None:
        response = self.table.get_item(Key={"note_id": note_id})
        item = response.get("Item")
        if not item:
            return None
        return self._deserialize(item)

    def list_notes(self) -> List[NoteOut]:
        response = self.table.scan()
        items = response.get("Items", [])
        return [self._deserialize(item) for item in items]

    def update_note(self, note_id: str, payload: NoteUpdate) -> NoteOut | None:
        existing_response = self.table.get_item(Key={"note_id": note_id})
        item = existing_response.get("Item")
        if not item:
            return None

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
        self.table.put_item(Item=updated)
        return self._deserialize(updated)

    def delete_note(self, note_id: str) -> bool:
        response = self.table.delete_item(Key={"note_id": note_id})
        return response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200

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
