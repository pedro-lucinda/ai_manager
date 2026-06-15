"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_GMAIL_SCOPES = ["https://mail.google.com/"]
DEFAULT_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0
    openai_max_retries: int = 2

    gmail_client_id: str
    gmail_client_secret: str
    oauth_port: int = Field(default=8080, validation_alias="GMAIL_OAUTH_PORT")

    gmail_scopes: list[str] = DEFAULT_GMAIL_SCOPES
    gmail_token_file: str = "token.json"

    calendar_scopes: list[str] = DEFAULT_CALENDAR_SCOPES
    calendar_token_file: str = "token_calendar.json"

    @field_validator("gmail_scopes", "calendar_scopes", mode="before")
    @classmethod
    def parse_comma_separated_scopes(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if not str(value).strip():
            return []
        return [scope.strip() for scope in str(value).split(",") if scope.strip()]

    @model_validator(mode="after")
    def apply_scope_defaults(self) -> Settings:
        if not self.gmail_scopes:
            self.gmail_scopes = list(DEFAULT_GMAIL_SCOPES)
        if not self.calendar_scopes:
            self.calendar_scopes = list(DEFAULT_CALENDAR_SCOPES)
        return self

    @field_validator("oauth_port")
    @classmethod
    def validate_oauth_port(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("oauth_port must be a positive integer.")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
