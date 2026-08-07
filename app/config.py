from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized app config. Values are loaded from environment variables
    (or a .env file) automatically thanks to pydantic-settings.
    """

    llm_provider: str = "ollama"  # "openai" or "ollama"

    # OpenAI-compatible settings (also used for Groq/Grok/etc via base_url override)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Ollama settings (local, free, no key needed)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Single shared instance imported across the app
settings = Settings()
