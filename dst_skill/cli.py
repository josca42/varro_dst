from __future__ import annotations

import argparse
import json

import httpx

from dst_skill.config import column_values_token, column_values_url


def parse_args():
    parser = argparse.ArgumentParser(
        prog="dst-column-values",
        description="Look up Danmarks Statistik coded column values.",
    )
    parser.add_argument("table")
    parser.add_argument("column")
    parser.add_argument("--q", "--query", dest="query")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--for-table")
    parser.add_argument("--token", default=column_values_token())
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def fetch_json(args):
    headers = {"Accept": "application/json"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    params = {
        "table": args.table,
        "column": args.column,
        "n": args.n,
    }
    if args.query:
        params["q"] = args.query
    if args.for_table:
        params["for_table"] = args.for_table

    response = httpx.get(
        f"{column_values_url().rstrip('/')}/v1/column-values",
        params=params,
        headers=headers,
        timeout=30,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise SystemExit(
                "Column-values authentication failed. Run dst-setup again or set "
                "DST_COLUMN_VALUES_TOKEN."
            ) from None
        raise
    return response.json()


def rows_from_payload(payload):
    for key in ("rows", "values", "matches"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows
    if isinstance(payload, list):
        return payload
    return []


def format_value(value):
    return "" if value is None else str(value)


def print_table(payload):
    rows = rows_from_payload(payload)
    if not rows:
        print("<no values>")
        return

    keys = list(rows[0].keys())
    for row in rows[1:]:
        for key in row:
            if key not in keys:
                keys.append(key)

    widths = {
        key: max(len(key), *(len(format_value(row.get(key))) for row in rows))
        for key in keys
    }

    title_parts = []
    for key in ("table", "column", "for_table", "fact_column", "filtered"):
        if key in payload and payload[key] not in (None, ""):
            title_parts.append(f"{key}: {payload[key]}")
    if title_parts:
        print(" | ".join(title_parts))

    print(" | ".join(key.ljust(widths[key]) for key in keys))
    print(" | ".join("-" * widths[key] for key in keys))
    for row in rows:
        print(" | ".join(format_value(row.get(key)).ljust(widths[key]) for key in keys))


def main():
    args = parse_args()
    payload = fetch_json(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_table(payload)
