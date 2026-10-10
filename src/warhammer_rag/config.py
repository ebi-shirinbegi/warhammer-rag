"""Local configuration; importing this module never calls an external service."""

from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """Locate the source checkout, with cwd as a fallback for wheel installations."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "data" / "raw").is_dir():
            return parent
    return Path.cwd()


class Settings(BaseSettings):
    """Read environment variables and .env in the current working directory."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

    google_api_key: SecretStr | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    google_model: str | None = Field(default=None, validation_alias="GOOGLE_MODEL")
    project_root: Path = Field(default_factory=_project_root, validation_alias="RAG_PROJECT_ROOT")
    raw_dir: Path = Field(default=Path("data/raw"), validation_alias="RAG_RAW_DIR")
    processed_dir: Path = Field(
        default=Path("data/processed"), validation_alias="RAG_PROCESSED_DIR"
    )
    index_dir: Path = Field(default=Path("data/indexes"), validation_alias="RAG_INDEX_DIR")
    eval_dir: Path = Field(default=Path("evaluation/datasets"), validation_alias="RAG_EVAL_DIR")
    report_dir: Path = Field(default=Path("evaluation/reports"), validation_alias="RAG_REPORT_DIR")

    @field_validator("google_model", mode="before")
    @classmethod
    def normalize_optional_model(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def resolve_directories(self) -> Self:
        self.project_root = self.project_root.expanduser().resolve()
        for name in ("raw_dir", "processed_dir", "index_dir", "eval_dir", "report_dir"):
            value = getattr(self, name).expanduser()
            if not value.is_absolute():
                value = self.project_root / value
            setattr(self, name, value.resolve())
        return self

    @property
    def has_api_key(self) -> bool:
        return self.google_api_key is not None and bool(
            self.google_api_key.get_secret_value().strip()
        )

    @property
    def rulebook_path(self) -> Path:
        return self.raw_dir / "core_rules.pdf"

    @property
    def database_path(self) -> Path:
        return self.raw_dir / "wahadb.sqlite"
