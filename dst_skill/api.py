from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from dst_skill import __version__
from dst_skill.column_values import column_values, column_values_dir, docs_dir

app = FastAPI(title="Danmarks Statistik Column Values", version=__version__)


def _split_tokens(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [
        token.strip()
        for token in raw.replace("\n", ",").split(",")
        if token.strip()
    ]


def configured_tokens() -> list[str]:
    tokens = _split_tokens(os.environ.get("DST_COLUMN_VALUES_TOKENS"))
    tokens.extend(_split_tokens(os.environ.get("DST_COLUMN_VALUES_TOKEN")))

    token_file = os.environ.get("DST_COLUMN_VALUES_TOKEN_FILE")
    if token_file:
        path = Path(token_file).expanduser()
        if path.exists():
            tokens.extend(_split_tokens(path.read_text()))

    return tokens


def auth_required() -> bool:
    value = os.environ.get("DST_COLUMN_VALUES_REQUIRE_TOKEN", "").lower()
    return value in {"1", "true", "yes", "on"} or bool(configured_tokens())


def require_auth(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    tokens = configured_tokens()
    if not tokens and not auth_required():
        return
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Column-values auth is required but no token is configured.",
        )

    supplied = x_api_key
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            supplied = value.strip()

    if supplied and any(secrets.compare_digest(supplied, token) for token in tokens):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/version")
def version(_auth: None = Depends(require_auth)):
    return {
        "version": __version__,
        "docs_dir": str(docs_dir()),
        "column_values_dir": str(column_values_dir()),
    }


@app.get("/v1/column-values")
def get_column_values(
    table: str,
    column: str,
    q: str | None = None,
    fuzzy_match_str: str | None = None,
    n: int = Query(5, ge=1, le=100),
    for_table: str | None = None,
    _auth: None = Depends(require_auth),
):
    return column_values(
        table=table,
        column=column,
        q=q or fuzzy_match_str,
        n=n,
        for_table=for_table,
    )


def main():
    host = os.environ.get("DST_COLUMN_VALUES_HOST", "127.0.0.1")
    port = int(os.environ.get("DST_COLUMN_VALUES_PORT", "8010"))
    uvicorn.run("dst_skill.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
