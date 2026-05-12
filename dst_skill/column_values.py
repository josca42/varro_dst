from __future__ import annotations

import json
import os
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
from rapidfuzz import process

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def normalize_table_name(table: str) -> str:
    return table.strip().lower().replace("fact.", "").replace("dim.", "")


def normalize_column_name(name: str) -> str:
    return name.lower().replace("å", "a").replace("ø", "o").replace("æ", "ae")


def docs_dir() -> Path:
    env = os.environ.get("DST_DOCS_DIR")
    candidates = [
        Path(env).expanduser() if env else None,
        PLUGIN_ROOT / "docs",
        PLUGIN_ROOT.parent / "agent_data",
        Path.cwd() / "docs",
    ]
    for candidate in candidates:
        if candidate and (candidate / "column_values").exists():
            return candidate.resolve()
    return (PLUGIN_ROOT / "docs").resolve()


def dimension_links_dir() -> Path:
    env = os.environ.get("DST_DIMENSION_LINKS_DIR")
    candidates = [
        Path(env).expanduser() if env else None,
        docs_dir() / "dimension_links",
        PLUGIN_ROOT.parent / "data" / "dst" / "dimension_links",
        Path.cwd() / "data" / "dst" / "dimension_links",
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate.resolve()
    return (docs_dir() / "dimension_links").resolve()


def column_values_dir() -> Path:
    return docs_dir() / "column_values"


def dim_tables() -> set[str]:
    return {path.stem for path in column_values_dir().glob("*.parquet")}


def load_dimension_links(table: str) -> dict[str, str]:
    path = dimension_links_dir() / f"{table.upper()}.json"
    if not path.exists():
        return {}
    entries = json.loads(path.read_text())
    return {
        normalize_column_name(entry["column"]): entry["dimension"].strip().lower()
        for entry in entries
    }


def fact_value_files(table: str) -> list[Path]:
    return sorted((column_values_dir() / table).glob("*.parquet"))


def infer_fact_column_for_dim(df: pd.DataFrame, dim_table: str, for_table: str) -> str:
    files = fact_value_files(for_table)
    columns = [file.stem for file in files]

    prefix_matches = sorted(col for col in columns if dim_table.startswith(col))
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    ranked_names = sorted(
        ((col, SequenceMatcher(None, col, dim_table).ratio()) for col in columns),
        key=lambda item: item[1],
        reverse=True,
    )
    if ranked_names and ranked_names[0][1] >= 0.7:
        return ranked_names[0][0]

    codes = {str(code) for code in df["kode"].dropna()}
    ranked_overlaps = []
    for file in files:
        values = pd.read_parquet(file)
        if "id" in values:
            value_ids = {str(value) for value in values["id"].dropna()}
            overlap = len(value_ids & codes)
            ratio = overlap / len(value_ids) if value_ids else 0
            ranked_overlaps.append((file.stem, overlap, ratio))

    ranked_overlaps.sort(key=lambda item: (item[1], item[2]), reverse=True)
    if ranked_overlaps and ranked_overlaps[0][1] > 0:
        return ranked_overlaps[0][0]

    raise ValueError(
        f"Could not infer a fact column in {for_table!r} for dim {dim_table!r}."
    )


def filter_dimension_values(
    df: pd.DataFrame, dim_table: str, for_table: str
) -> tuple[pd.DataFrame, str]:
    links = load_dimension_links(for_table)
    fact_columns = sorted(col for col, dim in links.items() if dim == dim_table)
    fact_column = (
        fact_columns[0]
        if fact_columns
        else infer_fact_column_for_dim(df, dim_table, for_table)
    )
    fact_values = pd.read_parquet(
        column_values_dir() / for_table / f"{fact_column}.parquet"
    )
    codes = {str(code) for code in fact_values["id"].dropna()}
    return df[df["kode"].astype(str).isin(codes)], fact_column


def records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", force_ascii=False))


def value_rows(df: pd.DataFrame, schema: str, query: str | None, n: int) -> list[dict]:
    if not query:
        return records(df.head(n))

    search_col = "titel" if schema == "dim" else "text"
    choices = df[search_col].fillna("").astype(str).tolist()
    matches = process.extract(query, choices, limit=n)
    rows = []
    for _, score, index in matches:
        row = records(df.iloc[[index]])[0]
        row["score"] = round(score, 1)
        rows.append(row)
    return rows


def column_values(
    table: str,
    column: str,
    q: str | None = None,
    n: int = 5,
    for_table: str | None = None,
) -> dict:
    table = normalize_table_name(table)
    for_table = normalize_table_name(for_table) if for_table else None

    if table in dim_tables():
        df = pd.read_parquet(column_values_dir() / f"{table}.parquet")
        schema = "dim"
        fact_column = None
        if for_table:
            df, fact_column = filter_dimension_values(df, table, for_table)
    else:
        df = pd.read_parquet(column_values_dir() / table / f"{column}.parquet")
        schema = "fact"
        fact_column = None

    return {
        "table": table,
        "column": column,
        "schema": schema,
        "q": q,
        "n": n,
        "for_table": for_table,
        "fact_column": fact_column,
        "filtered": bool(for_table and schema == "dim"),
        "rows": value_rows(df, schema, q, n),
    }
