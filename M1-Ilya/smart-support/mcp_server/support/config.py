"""Configuration only via environment variables. No secrets here."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_TRANSPORTS = ("stdio", "streamable-http")


@dataclass(frozen=True)
class Settings:
    db_path: Path
    transport: str
    http_host: str
    http_port: int
    log_level: str

    @staticmethod
    def from_env(env: dict[str, str] | None = None) -> "Settings":
        env = dict(os.environ) if env is None else env
        raw_db = env.get("SUPPORT_DB_PATH") or "./data/support.sqlite"
        db_path = Path(raw_db)
        if not db_path.is_absolute():
            db_path = (REPO_ROOT / db_path).resolve()
        transport = env.get("MCP_TRANSPORT") or "stdio"
        if transport not in VALID_TRANSPORTS:
            raise ValueError(f"MCP_TRANSPORT must be one of {VALID_TRANSPORTS}, got {transport!r}")
        return Settings(
            db_path=db_path,
            transport=transport,
            http_host=env.get("MCP_HTTP_HOST") or "127.0.0.1",
            http_port=int(env.get("MCP_HTTP_PORT") or "8000"),
            log_level=(env.get("MCP_LOG_LEVEL") or "INFO").upper(),
        )
