from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from dst_skill.config import (
    DEFAULT_COLUMN_VALUES_URL,
    DEFAULT_DB_HOST,
    DEFAULT_DB_NAME,
    DEFAULT_DB_PORT,
    DEFAULT_DB_USER,
    dashboards_dir,
    sqlalchemy_url,
)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="dst-setup",
        description="Configure a workspace for the hosted Varro DST database and API.",
    )
    parser.add_argument("--token", help="DST auth token. Prompts securely if omitted.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--dashboards-dir", type=Path)
    parser.add_argument("--no-gitignore", action="store_true")
    return parser.parse_args()


def _write_secret(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o600)


def _add_gitignore(project_dir: Path, dashboards: Path) -> None:
    gitignore = project_dir / ".gitignore"
    try:
        rel_path = dashboards.relative_to(project_dir).as_posix()
    except ValueError:
        return

    line = f"{rel_path}/.varro/"
    existing = gitignore.read_text().splitlines() if gitignore.exists() else []
    if line not in existing:
        existing.append(line)
        gitignore.write_text("\n".join(existing).rstrip() + "\n")


def main():
    args = parse_args()
    project_dir = args.project_dir.expanduser().resolve()
    dashboards = (
        args.dashboards_dir.expanduser().resolve()
        if args.dashboards_dir
        else dashboards_dir(project_dir)
    )
    config_dir = dashboards / ".varro"

    token = args.token or getpass.getpass("DST auth token: ")
    if not token:
        raise SystemExit("No token provided.")

    connection = sqlalchemy_url(
        token=token,
    )
    _write_secret(
        config_dir / "sql_connection.txt",
        "# Hosted Varro DST PostgreSQL connection.\n"
        "# Used by the Varro SQL MCP tool.\n"
        f"{connection}\n",
    )
    _write_secret(
        config_dir / "dst.env",
        "# Hosted Varro DST column-values API.\n"
        f"DST_COLUMN_VALUES_URL={DEFAULT_COLUMN_VALUES_URL}\n"
        f"DST_COLUMN_VALUES_TOKEN={token}\n"
        f"DST_DB_HOST={DEFAULT_DB_HOST}\n"
        f"DST_DB_PORT={DEFAULT_DB_PORT}\n"
        f"DST_DB_NAME={DEFAULT_DB_NAME}\n"
        f"DST_DB_USER={DEFAULT_DB_USER}\n",
    )
    config_dir.chmod(0o700)

    if not args.no_gitignore:
        _add_gitignore(project_dir, dashboards)

    print(f"Wrote {config_dir / 'sql_connection.txt'}")
    print(f"Wrote {config_dir / 'dst.env'}")
    print("Verify with: dst-column-values befolk1 kon --n 3")
    print("Verify SQL with the Varro MCP tool: select 1 as ok")


if __name__ == "__main__":
    main()
