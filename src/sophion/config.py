"""Configuration management for Sophion."""

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass
class BackendConfig:
    """LLM backend configuration."""

    primary: str = "claude-code"
    api_provider: str | None = None
    api_key: str | None = None
    model: str | None = None


@dataclass
class StudyConfig:
    """Study mode configuration."""

    enabled: bool = False
    socratic: bool = False
    proof_verification: bool = False


@dataclass
class Config:
    """Top-level Sophion configuration."""

    base_dir: Path = field(default_factory=lambda: Path.home() / ".sophion")
    backend: BackendConfig = field(default_factory=BackendConfig)
    study: StudyConfig = field(default_factory=StudyConfig)

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Config":
        """Load config from TOML file with optional base_dir override."""
        if base_dir is None:
            base_dir = Path.home() / ".sophion"

        config_path = base_dir / "config.toml"

        if config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            return cls._from_dict(data, base_dir)

        return cls(base_dir=base_dir)

    @classmethod
    def _from_dict(cls, data: dict, base_dir: Path) -> "Config":
        backend_data = data.get("backend", {})
        study_data = data.get("study", {})

        return cls(
            base_dir=base_dir,
            backend=BackendConfig(
                primary=backend_data.get("primary", "claude-code"),
                api_provider=backend_data.get("api_provider"),
                api_key=backend_data.get("api_key"),
                model=backend_data.get("model"),
            ),
            study=StudyConfig(
                enabled=study_data.get("enabled", False),
                socratic=study_data.get("socratic", False),
                proof_verification=study_data.get("proof_verification", False),
            ),
        )
