from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

DEFAULT_COLUMN_VALUES_URL = "https://varro.dk/dst"
DEFAULT_DB_HOST = "varro.dk"
DEFAULT_DB_PORT = 5432
DEFAULT_DB_NAME = "dst"
DEFAULT_DB_USER = "dstread"


def dashboards_dir(project_dir: Path | None = None) -> Path:
    env = os.environ.get("VARRO_DASHBOARDS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return ((project_dir or Path.cwd()) / "dashboards").resolve()


def varro_config_dir(project_dir: Path | None = None) -> Path:
    return dashboards_dir(project_dir) / ".varro"


def _ancestor_dirs(start: Path | None = None):
    path = (start or Path.cwd()).resolve()
    if path.is_file():
        path = path.parent
    yield path
    yield from path.parents


def workspace_config_candidates(start: Path | None = None) -> list[Path]:
    candidates: list[Path] = []
    env_dashboards_dir = os.environ.get("VARRO_DASHBOARDS_DIR")
    if env_dashboards_dir:
        candidates.append(Path(env_dashboards_dir).expanduser() / ".varro" / "dst.env")

    for root in _ancestor_dirs(start):
        candidates.append(root / "dashboards" / ".varro" / "dst.env")
        candidates.append(root / ".varro" / "dst.env")

    seen: set[Path] = set()
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def workspace_settings(start: Path | None = None) -> dict[str, str]:
    for candidate in workspace_config_candidates(start):
        if candidate.exists():
            return read_env_file(candidate)
    return {}


def column_values_url(start: Path | None = None) -> str:
    return (
        workspace_settings(start).get("DST_COLUMN_VALUES_URL")
        or DEFAULT_COLUMN_VALUES_URL
    )


def column_values_token(start: Path | None = None) -> str | None:
    return os.environ.get("DST_COLUMN_VALUES_TOKEN") or workspace_settings(start).get(
        "DST_COLUMN_VALUES_TOKEN"
    )


def sqlalchemy_url(
    token: str,
    host: str = DEFAULT_DB_HOST,
    port: int = DEFAULT_DB_PORT,
    database: str = DEFAULT_DB_NAME,
    user: str = DEFAULT_DB_USER,
) -> str:
    quoted_user = quote(user, safe="")
    quoted_token = quote(token, safe="")
    quoted_database = quote(database, safe="")
    return (
        f"postgresql+psycopg://{quoted_user}:{quoted_token}"
        f"@{host}:{port}/{quoted_database}?sslmode=require"
    )
