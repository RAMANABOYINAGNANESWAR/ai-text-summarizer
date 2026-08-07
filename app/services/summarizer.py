from openai import OpenAI, APIConnectionError, APIStatusError

from app.config import settings

SYSTEM_PROMPT = (
    "You are a precise summarization engine. Summarize the user's text "
    "clearly and factually. Do not add opinions or information that isn't "
    "in the original text. Return only the summary, no preamble."
)


def _get_client() -> tuple[OpenAI, str]:
    """
    Returns a configured OpenAI-SDK client and the model name to use.
    Ollama exposes an OpenAI-compatible endpoint at /v1, so the same
    SDK works for both real OpenAI-style providers and local Ollama.
    """
    if settings.llm_provider == "ollama":
        client = OpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",  # required by SDK, unused by Ollama
        )
        model = settings.ollama_model
    elif settings.llm_provider == "openai":
        client = OpenAI(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        )
        model = settings.openai_model
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")

    return client, model


def summarize_text(text: str, max_words: int = 60) -> str:
    """
    Calls the configured LLM to summarize `text` in roughly `max_words` words.
    Raises RuntimeError on any upstream failure so the API layer can turn it
    into a clean HTTP error.
    """
    client, model = _get_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Summarize the following text in about {max_words} words:\n\n{text}"
                    ),
                },
            ],
            temperature=0.3,
        )
    except APIConnectionError as e:
        raise RuntimeError(
            "Could not reach the LLM provider. If using Ollama, make sure "
            "'ollama serve' is running. If using OpenAI, check your network."
        ) from e
    except APIStatusError as e:
        raise RuntimeError(f"LLM provider returned an error: {e.message}") from e

    summary = response.choices[0].message.content
    if not summary:
        raise RuntimeError("LLM returned an empty response.")

    return summary.strip()
