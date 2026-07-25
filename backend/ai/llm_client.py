"""
Groq LLM client — swappable via config.
Supports Groq (default), with easy extension to OpenAI/Gemini.
"""
import logging
from typing import Optional
import httpx

from backend.config import get_settings
from backend.utils.exceptions import LLMError

logger = logging.getLogger("patentpilot.ai.llm_client")
settings = get_settings()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = None,
    temperature: float = None,
) -> str:
    """
    Call Groq API (OpenAI-compatible) and return the response text.
    Raises LLMError on failure.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens or settings.GROQ_MAX_TOKENS,
        "temperature": temperature or settings.GROQ_TEMPERATURE,
    }

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code != 200:
                error_text = resp.text[:500]
                logger.error(f"Groq API error {resp.status_code}: {error_text}")
                raise LLMError(f"Groq API returned {resp.status_code}: {error_text}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            logger.info(f"Groq call successful, tokens used: {tokens_used}")
            return content.strip()
    except LLMError:
        raise
    except httpx.TimeoutException:
        raise LLMError("Groq API request timed out after 60 seconds")
    except Exception as e:
        raise LLMError(f"Unexpected LLM error: {str(e)}")
