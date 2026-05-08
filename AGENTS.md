# Varro DST Skill

Read `SKILL.md` first.

`docs/subjects`, `docs/fact`, `docs/dim`, `docs/geo`, `docs/subject_hierarchy.md`, and `docs/table_index.jsonl` are generated from the Varro repo's root `agent_data/`.

Do not hand-edit generated `docs` files. Update the source data or run:

```bash
python3 scripts/sync_docs.py
```

The skill depends on the Varro plugin for SQL, Jupyter, and dashboards. Keep this repo focused on Danmarks Statistik domain guidance, reference docs, geofiles, and the column-values CLI.

Run the local column-values API with:

```bash
uv run dst-column-values-api
```

Set `DST_DOCS_DIR` if `docs/column_values` is not available in this skill folder or the parent Varro repo.
