# Varro DST Skill

Read `skills/dst/SKILL.md` first.

`docs/subjects`, `docs/fact`, `docs/dim`, `docs/geo`, `docs/subjects/index.md`, and `docs/geo/index.md` are generated from the Varro repo's root `agent_data/`.

Do not hand-edit generated `docs` files. Update the source data or run:

```bash
python3 scripts/sync_docs.py
```

The skill depends on the Varro plugin for SQL, Jupyter, and dashboards. Keep this repo focused on Danmarks Statistik domain guidance, reference docs, geofiles, and the column-values CLI.

For user workspaces, DST access is hosted-only. Codex should configure the Varro SQL connection for `varro.dk:5432` and use the column-values API at `https://varro.dk/dst` via `dst-setup`; do not document or suggest a local API/database path for normal use.
