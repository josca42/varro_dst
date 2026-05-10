# Varro DST Workspace Setup

Use this when a workspace needs access to the hosted Varro DST services.

Hosted defaults:

```text
PostgreSQL: varro.dk:5432 database dst user dstread
Column values API: https://varro.dk/dst
```

The same DST auth token is used as the PostgreSQL password and as the
column-values API bearer token unless the server administrator says otherwise.
This skill is designed for the hosted services only: Codex should connect to
PostgreSQL on `varro.dk:5432` and the column-values API at
`https://varro.dk/dst`, not to a local database or local API process.

## Procedure

1. Ask the user for the DST auth token.
2. From the user's project workspace, run the skill setup helper:

```bash
uv run --project /path/to/varro_dst dst-setup
```

If you already have the token in a safe variable:

```bash
uv run --project /path/to/varro_dst dst-setup --token "$DST_AUTH_TOKEN"
```

The helper writes:

```text
dashboards/.varro/sql_connection.txt  # Varro SQL MCP connection string
dashboards/.varro/dst.env             # column-values API URL and token
```

It also adds `dashboards/.varro/` to `.gitignore` when the dashboards directory
is inside the workspace.

## Verify

Run a column-values lookup from the workspace:

```bash
uv run --project /path/to/varro_dst dst-column-values befolk1 kon --n 3
```

Then use the Varro SQL MCP tool:

```sql
select 1 as ok;
```

For a DST smoke test:

```sql
select count(*) as rows from fact.befolk1;
```

## Notes

- Never commit files under `dashboards/.varro/`.
- If the user has a non-default dashboard location, set `VARRO_DASHBOARDS_DIR`
  before running `dst-setup`, or pass `--dashboards-dir`.
- The CLI reads `DST_COLUMN_VALUES_TOKEN` or the workspace config file written
  by `dst-setup`.
