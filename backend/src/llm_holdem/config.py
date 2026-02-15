"""Configuration and environment variable management."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env file from project root
_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./llm_holdem.db",
        description="Database connection URL",
    )

    # LLM Provider API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    google_api_key: str = Field(default="", description="Google AI API key")
    groq_api_key: str = Field(default="", description="Groq API key")
    mistral_api_key: str = Field(default="", description="Mistral API key")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Logfire
    logfire_token: str = Field(default="", description="Pydantic Logfire token")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def available_providers(self) -> list[str]:
        """Return list of providers with configured API keys."""
        providers: list[str] = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.google_api_key:
            providers.append("google")
        if self.groq_api_key:
            providers.append("groq")
        if self.mistral_api_key:
            providers.append("mistral")
        # Ollama is always "available" — we'll check connectivity at runtime
        providers.append("ollama")
        return providers


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
