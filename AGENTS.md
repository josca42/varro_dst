# Varro DST Skill

Read `skills/varro-dst/SKILL.md` first.

`skills/varro-dst/docs/subjects`, `skills/varro-dst/docs/fact`, `skills/varro-dst/docs/dim`, `skills/varro-dst/docs/geo`, `skills/varro-dst/docs/subject_hierarchy.md`, and `skills/varro-dst/docs/table_index.jsonl` are generated from the Varro repo's root `agent_data/`.

Do not hand-edit generated `docs` files. Update the source data or run:

```bash
python3 scripts/sync_docs.py
```

The skill depends on the Varro plugin for SQL, Jupyter, and dashboards. Keep this repo focused on Danmarks Statistik domain guidance, reference docs, geofiles, and the column-values CLI.

For user workspaces, DST access is hosted-only. Codex should configure the Varro SQL connection for `varro.dk:5432` and use the column-values API at `https://varro.dk/dst` via `dst-setup`; do not document or suggest a local API/database path for normal use.
