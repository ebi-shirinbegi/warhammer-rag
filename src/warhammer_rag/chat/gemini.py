"""Minimal connection check for the configured Google AI Studio backend."""

from google import genai
from google.genai import types

from warhammer_rag.chat.throttle import wait_for_slot
from warhammer_rag.config import Settings


def check_connection(settings: Settings) -> bool:
    """Make one small request; the caller must explicitly opt into API usage."""
    if not settings.has_api_key or not settings.google_model:
        raise ValueError("Configure GOOGLE_API_KEY and GOOGLE_MODEL in .env.")
    wait_for_slot(
        settings.project_root / "data/local/api_throttle.sqlite",
        settings.google_requests_per_minute,
    )
    with genai.Client(api_key=settings.google_api_key.get_secret_value()) as client:
        response = client.models.generate_content(
            model=settings.google_model,
            contents="Reply with only OK.",
            config=types.GenerateContentConfig(max_output_tokens=512),
        )
    return bool(response.text and response.text.strip() == "OK")
