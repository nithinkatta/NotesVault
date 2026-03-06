from __future__ import annotations

import json

import httpx
import google.generativeai as genai

from app.config import Settings


def _model(settings: Settings):
    """Return configured Gemini model instance."""
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


async def summarize_text(settings: Settings, content: str) -> dict:
    """Return summary and keywords for provided text content."""
    model = _model(settings)
    prompt = (
        "Summarize the user-provided note into 2-3 sentences and extract 5-8 relevant "
        "keywords. Respond strictly as JSON with keys 'summary' and 'keywords'."
    )
    response = await model.generate_content_async(
        [{"text": prompt}, {"text": content}],
        generation_config={"temperature": 0.2},
    )
    raw = response.text or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"summary": raw.strip(), "keywords": []}
    return {
        "summary": parsed.get("summary", "").strip(),
        "keywords": parsed.get("keywords", []),
    }


async def perform_ocr(settings: Settings, image_url: str) -> str:
    """Extract text from an image URL using a vision model."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        image_bytes = resp.content
        mime_type = resp.headers.get("content-type", "image/png")

    model = _model(settings)
    response = await model.generate_content_async(
        [
            {"text": "Extract all visible text from the provided image. Return only the text."},
            {"mime_type": mime_type, "data": image_bytes},
        ],
        generation_config={"temperature": 0},
    )
    return (response.text or "").strip()


async def transcribe_audio(settings: Settings, audio_url: str) -> str:
    """Transcribe audio from a URL using Gemini."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        audio_bytes = resp.content
        mime_type = resp.headers.get("content-type", "audio/mpeg")

    model = _model(settings)
    response = await model.generate_content_async(
        [
            {"text": "Transcribe the audio content into text. Return only the transcription."},
            {"mime_type": mime_type, "data": audio_bytes},
        ],
        generation_config={"temperature": 0},
    )
    return (response.text or "").strip()
