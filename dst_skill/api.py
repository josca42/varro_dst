from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from dst_skill import __version__
from dst_skill.column_values import column_values, column_values_dir, docs_dir

app = FastAPI(title="Danmarks Statistik Column Values", version=__version__)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/version")
def version():
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
    n: int = 5,
    for_table: str | None = None,
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
