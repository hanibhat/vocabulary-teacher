import json
import logging
import re
import time

import httpx

from config import config

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRYABLE_STATUSES = {429, 503}
MAX_RETRIES = 3
RETRY_DELAYS = [5, 10, 20]


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        pass
    else:
        if isinstance(result, dict):
            return result
        raise ValueError(
            f"Expected a JSON object, got {type(result).__name__}: {text[:300]}"
        )
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(1).strip())
            if not isinstance(result, dict):
                raise ValueError(f"Expected a JSON object, got {type(result).__name__}")
            return result
        except json.JSONDecodeError:
            pass
    raise ValueError(f"LLM response was not valid JSON: {text[:300]}")


def _is_retryable(error: Exception) -> bool:
    msg = str(error)
    for code in RETRYABLE_STATUSES:
        if str(code) in msg:
            return True
    return False


def _build_prompt(word: str) -> str:
    return (
        f'You are a language learning assistant. For the German word "{word}", '
        "first correct it: add the article (der/die/das) if it is a noun, "
        "fix capitalization and spelling. "
        "Provide the corrected German word, the English translation and Arabic translation "
        "(in Arabic script, including articles where applicable). "
        "If there are multiple synonyms, separate them with commas (e.g. 'to allow, permit'), "
        "and allow only 2 max synonyms. "
        "Also provide a short natural example sentence in German using the corrected word, "
        "and its English and Arabic translations using the translated words.\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        '  "corrected_german": "der, die or das Word (corrected form with article)",\n'
        '  "english": "english translation (with article for nouns)",\n'
        '  "arabic": "arabic translation in Arabic script (with article for nouns)",\n'
        '  "example_german": "German example sentence using the corrected word",\n'
        '  "example_english": "English example sentence",\n'
        '  "example_arabic": "Arabic example sentence in Arabic script only"\n'
        "}"
    )


def translate_and_generate(word: str) -> dict:
    prompt = _build_prompt(word)
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = httpx.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {config.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": config.openrouter_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]

            return _parse_json_response(text)
        except Exception as e:
            last_error = e
            if not _is_retryable(e) or attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_DELAYS[attempt]
            logger.warning(
                "OpenRouter API error (attempt %d/%d): %s. Retrying in %ds...",
                attempt + 1,
                MAX_RETRIES,
                e,
                delay,
            )
            time.sleep(delay)

    raise last_error
