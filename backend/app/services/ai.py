from __future__ import annotations

import json
from io import BytesIO

import httpx
from openai import AsyncOpenAI

from app.config import Settings


def _client(settings: Settings) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def summarize_text(settings: Settings, content: str) -> dict:
    """Return summary and keywords for provided text content."""
    client = _client(settings)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize the user-provided note into 2-3 sentences and extract 5-8 "
                    "relevant keywords. Respond as JSON with keys 'summary' and 'keywords'."
                ),
            },
            {"role": "user", "content": content},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)
    return {
        "summary": parsed.get("summary", "").strip(),
        "keywords": parsed.get("keywords", []),
    }


async def perform_ocr(settings: Settings, image_url: str) -> str:
    """Extract text from an image URL using a vision model."""
    client = _client(settings)
    response = await client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "Extract all visible text from the provided image.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the text from this image."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


async def transcribe_audio(settings: Settings, audio_url: str) -> str:
    """Transcribe audio from a URL using Whisper."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        audio_bytes = resp.content

    audio_file = BytesIO(audio_bytes)
    audio_file.name = "upload_audio.mp3"

    client = _client(settings)
    transcription = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return transcription.text.strip()
