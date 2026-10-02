import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JevConfig:
    """Configuration without storing or exposing secret values in repr/logs."""

    api_key: str | None = None
    base_url: str = "https://api.typesafe.ai"
    model: str = "jev-latest"
    timeout_seconds: float = 10.0
    min_confidence: float = 0.0

    @classmethod
    def from_environment(cls) -> "JevConfig":
        """Load environment variables and optional ~/.claude/jev.env.

        Environment variables take precedence over the optional file.
        """

        file_values = _read_env_file(Path.home() / ".claude" / "jev.env")
        env = {**file_values, **os.environ}

        api_key = (
            env.get("JEV_API_KEY")
            or env.get("TYPESAFE_API_KEY")
            or env.get("OPENROUTER_API_KEY")
        )
        base_url = env.get("TYPESAFE_BASE_URL") or "https://api.typesafe.ai"

        return cls(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            model=env.get("JEV_MODEL", "jev-latest"),
            timeout_seconds=float(env.get("JEV_TIMEOUT_SECONDS", "10")),
            min_confidence=float(env.get("JEV_MIN_CONFIDENCE", "0")),
        )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values
