# Varro DST Workspace Setup

Run this in each workspace that needs access to the hosted Danmarks Statistik
services.

## 1. Install the plugins

Install both plugins from the Varro marketplace:

- `varro`
- `varro-dst`

Core Varro must already be prepared with `uv` and Python. See
`varro_plugin/INSTALL.md` in the Varro marketplace checkout.

## 2. Configure DST credentials

From the workspace root, run the setup helper with the installed `varro-dst`
plugin path as the `--project` value:

```bash
uv run --project /path/to/varro_dst dst-setup
```

The command prompts securely for the DST auth token.

If the token is already in a shell variable:

```bash
uv run --project /path/to/varro_dst dst-setup --token "$DST_AUTH_TOKEN"
```

The helper writes:

```text
.varro/sql_connection.txt
.varro/dst.env
```

Both files are local workspace secrets and are written with `0600`
permissions. The `.varro/` directory is added to `.gitignore` unless
`--no-gitignore` is passed.

## 3. Verify

From the same workspace:

```bash
uv run --project /path/to/varro_dst dst-column-values befolk1 kon --n 3
```

Then verify SQL through the Varro MCP tool:

```sql
select 1 as ok;
```
