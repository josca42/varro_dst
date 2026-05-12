---
name: dst
description: Use when analyzing Danish official statistics from Danmarks Statistik or StatBank, especially with the Varro plugin SQL/Jupyter/dashboard tools. Provides the Rigsstatistiker workflow, table documentation navigation, safe SQL filter lookup via dst-column-values, geography files, and guardrails for fact/dim tables about Denmark.
---

# Danmarks Statistik

Use this skill as the domain layer for Danish official statistics. Use the Varro plugin for execution:

- `mcp__varro__sql` for PostgreSQL queries
- `mcp__varro__jupyter` for Python analysis
- `varro:dashboards` for persistent dashboard artifacts

Do not duplicate Varro plugin instructions here. Load the relevant Varro skill when you need tool-specific details.

This skill depends on the Varro plugin. Install and enable both `varro` and
`varro-dst` from the Varro Plugins marketplace.

If the workspace has not been configured for the hosted DST services yet, read
[setup.md](setup.md), ask the user for the DST auth token, and run `dst-setup`.

## Data Layout

Plugin-root paths. The `docs/` directory is next to `skills/`, not inside this
skill folder:

```text
docs/
├── subjects/          # Subject-level overviews (one .md per leaf subject)
│   ├── index.md       # Compact root -> mid overview
│   └── {root}/{mid}/{leaf}.md
├── fact/              # Per-table docs for fact tables
│   └── {root}/{mid}/{leaf}/{table_id}.md
├── dim/               # Dimension table docs
│   └── {table_id}.md
└── geo/               # GeoParquet boundary files for map visualizations
    ├── index.md
    └── {admin_region}.parquet
```

**subjects/** — Each leaf `.md` file lists all fact tables in that subject: linked dimension tables, table IDs, descriptions, columns, and time ranges. Use these to discover which tables are relevant for a topic.

**fact/** — Detailed documentation for one fact table: description, measure unit, all columns with valid values or dimension table links, and time range. Always read the relevant fact doc before writing SQL.

**dim/** — Dimension table docs. Describes hierarchy levels, kode/niveau/titel structure, and example values.

**geo/** — Simplified GeoParquet boundary files for Danish administrative regions (kommuner, regioner, landsdele). Each file is indexed by `dim_kode` matching `dim.nuts.kode`. Read `docs/geo/index.md` before creating map visualizations.

**Subject hierarchy:** Tables are organized into a 3-level tree: `root → mid → leaf → fact tables`. A compact overview of roots and mids is provided in `docs/subjects/index.md`. To discover leaves within a mid, use `Bash("ls docs/subjects/{root}/{mid}/")`.

IMPORTANT: Find the correct table by reading docs/subjects/index.md and then read the most likely leaf subject markdown file and from there read relevant fact tables and dim tables markdown files.

<database_schema>
Data is stored in PostgreSQL with two schemas:
- **dim.{table_id}** — Dimension tables (hierarchical groupings)
- **fact.{table_id}** — Fact tables (measurements and statistics)

### Dimension Tables
Store hierarchical groupings (regions, industries, education levels, etc.) with exactly 3 columns:

| Column | Description |
|--------|-------------|
| kode | Unique identifier (join key) |
| niveau | Hierarchy level (1 = most aggregated, higher = finer detail) |
| titel | Human-readable label |

Example hierarchy: niveau=1 "Regioner" → niveau=2 "Landsdele" → niveau=3 individual municipalities.

### Fact Tables
Contain statistical measurements with these column patterns:
- **indhold** — The measure/value (always present)
- **tid** — Time period (usually present)
- **Dimension columns** — Either:
  - Linked to dim table: `branche` → `JOIN dim.branche ON branche=kode`
  - Inline categorical: `køn` with values `['M', 'K']` (no join needed)

**Overcounting risk** — Most dimensions includes rows for both totals (e.g. `TOT`) and subcategories (e.g. `Mænd`, `Kvinder`). Always filter every dimension to either its total or its individual values — never sum across both.

### Join Pattern
```sql
SELECT f.indhold, d.titel
FROM fact.{table_id} f
JOIN dim.{dim_table} d ON f.{column} = d.kode
```
</database_schema>

Always let the data and table docs decide the method. Do not infer codes from labels.

## Column Values

Use the CLI for exact filter values and fuzzy label search:

```bash
uv run dst-column-values befolk1 kon
uv run dst-column-values nuts titel --for-table folk1a --q "kobenhavn" --n 10
uv run dst-column-values regkc dranst1 --q "folkeskole" --json
```

The CLI calls the hosted column-values API. By default it uses
`https://varro.dk/dst` and reads auth from `DST_COLUMN_VALUES_TOKEN` or the
workspace file written by `dst-setup` at `dashboards/.varro/dst.env`.
Use the hosted API and hosted PostgreSQL database over the internet; do not
start a local column-values API or configure the DST SQL connection to
`localhost`.

It mirrors the original Varro contract:

```text
ColumnValues(table, column, fuzzy_match_str?, n?, for_table?)
```

Use `--for-table` when browsing a shared dimension table for a specific fact table. This limits the dimension values to codes that actually occur in the fact table and avoids misleading full-taxonomy matches.

## SQL Guardrails

- Filter every non-target dimension to either total rows or one consistent level.
- Never sum totals and subcategories together.
- When joining dimensions with multiple `niveau` values, filter to one `niveau`.
- Use national aggregate rows directly when docs say the aggregate code is not in the dim table.
- Inline coded fact columns often do not join a dim table; use `dst-column-values`.
- For geography maps, read the fact doc and `docs/dim/nuts.md`, then merge with matching `dim_kode` in `docs/geo/*.parquet`.

## Output

- Answer in the user's language.
- Cite table IDs in prose, for example `(source: befolk1)`.
- When deriving rates, shares, or joins, say what was combined.
- Prefer a small table or chart over a long explanation.
