import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

TRANSLATION_PROMPT = (
    "Translate the following text to English. "
    "If it is already in English, return it exactly as-is. "
    "Return ONLY the translation, nothing else — no quotes, no explanation."
)


async def translate_text(text: str) -> str | None:
    """Translate text to English via OpenRouter.

    Returns the English translation, or None on any failure.
    Never raises — all errors are logged and swallowed.
    """
    if not text or not text.strip():
        return None

    if not settings.openrouter_api_key or not settings.translation_enabled:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.translation_model,
                    "messages": [
                        {"role": "system", "content": TRANSLATION_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.0,
                },
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
    except Exception:
        logger.warning("Translation failed for text: %s", text[:80], exc_info=True)
        return None
