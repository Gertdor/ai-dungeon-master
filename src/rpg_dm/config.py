"""Configuration management for the RPG DM system."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Application configuration."""

    # API Configuration (from environment)
    openrouter_api_key: str = Field(description="OpenRouter API key")

    # API endpoint
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Model Configuration
    dm_model: str = "anthropic/claude-4.5-sonnet"
    npc_model: str = "anthropic/claude-4-haiku"

    # Application Settings
    log_level: str = "INFO"
    data_dir: Path = Path("./data")

    # Model Parameters
    temperature: float = 0.7
    max_tokens: int = 2000

    def model_post_init(self, _context) -> None:
        """Initialize config and create necessary directories."""
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable must be set. "
                "Create a .env file or export it in your shell."
            )
        _config = Config(openrouter_api_key=api_key)
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance (useful for testing)."""
    global _config
    _config = config
