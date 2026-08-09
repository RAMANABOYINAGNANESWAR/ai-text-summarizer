import json

from openai import OpenAI, APIConnectionError, APIStatusError

from app.config import settings
from app.services.summarizer import _get_client

CLASSIFY_SYSTEM_PROMPT = (
    "You are a precise text classification engine. Given a piece of text "
    "(often a customer message), classify it and return ONLY a valid JSON "
    "object with exactly these keys: "
    '"intent" (a short label like "complaint", "question", "payment_issue", '
    '"praise", "other"), "priority" ("low", "medium", or "high"), '
    '"sentiment" ("positive", "neutral", or "negative"), and '
    '"requires_human" (true or false, true if the issue is urgent, sensitive, '
    "or the AI should not handle it alone). "
    "Return only the JSON object, no explanation, no markdown formatting."
)


def classify_text(text: str) -> dict:
    """
    Calls the configured LLM to classify `text` into intent/priority/
    sentiment/requires_human. Raises RuntimeError on any upstream failure
    so the API layer can turn it into a clean HTTP error.
    """
    client, model = _get_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0,
        )
    except APIConnectionError as e:
        raise RuntimeError(
            "Could not reach the LLM provider. If using Ollama, make sure "
            "'ollama serve' is running. If using OpenAI, check your network."
        ) from e
    except APIStatusError as e:
        raise RuntimeError(f"LLM provider returned an error: {e.message}") from e

    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("LLM returned an empty response.")

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM did not return valid JSON: {raw}") from e