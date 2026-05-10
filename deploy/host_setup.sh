#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo DST_AUTH_TOKEN=... bash deploy/host_setup.sh" >&2
  exit 1
fi

: "${DST_AUTH_TOKEN:?Set DST_AUTH_TOKEN to the shared DST auth token.}"

VARRO_DST_DIR="${VARRO_DST_DIR:-/home/dev/varro/varro_dst}"
UV_BIN="${UV_BIN:-/home/dev/.local/bin/uv}"
SERVICE_USER="${DST_SERVICE_USER:-dev}"
DB_NAME="${DST_DB_NAME:-dst}"
DB_USER="${DST_DB_USER:-dstread}"
API_PORT="${DST_COLUMN_VALUES_PORT:-8020}"
API_PREFIX="${DST_API_PREFIX:-/dst}"
DOMAIN="${DST_DOMAIN:-varro.dk}"

if [[ ! "$DB_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "Unsafe database name: $DB_NAME" >&2
  exit 1
fi
if [[ ! "$DB_USER" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "Unsafe database user: $DB_USER" >&2
  exit 1
fi
if [[ ! -d "$VARRO_DST_DIR" ]]; then
  echo "VARRO_DST_DIR does not exist: $VARRO_DST_DIR" >&2
  exit 1
fi

psql -h 127.0.0.1 -p 5432 -U postgres -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  --set=dst_token="$DST_AUTH_TOKEN" <<SQL
ALTER ROLE "$DB_USER" WITH LOGIN PASSWORD :'dst_token';
GRANT CONNECT ON DATABASE "$DB_NAME" TO "$DB_USER";
GRANT USAGE ON SCHEMA dim, fact TO "$DB_USER";
GRANT SELECT ON ALL TABLES IN SCHEMA dim, fact TO "$DB_USER";
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA dim GRANT SELECT ON TABLES TO "$DB_USER";
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA fact GRANT SELECT ON TABLES TO "$DB_USER";
ALTER DEFAULT PRIVILEGES FOR ROLE dstowner IN SCHEMA dim GRANT SELECT ON TABLES TO "$DB_USER";
ALTER DEFAULT PRIVILEGES FOR ROLE dstowner IN SCHEMA fact GRANT SELECT ON TABLES TO "$DB_USER";
SQL

cat >/etc/postgresql/18/main/conf.d/varro-public.conf <<'EOF'
# Varro DST public read-only access.
listen_addresses = '*'
password_encryption = scram-sha-256
EOF

if ! grep -q "Varro DST public read-only access" /etc/postgresql/18/main/pg_hba.conf; then
  cat >>/etc/postgresql/18/main/pg_hba.conf <<'EOF'

# Varro DST public read-only access.
hostssl dst dstread 0.0.0.0/0 scram-sha-256
hostssl dst dstread ::/0 scram-sha-256
EOF
fi

install -d -m 0755 /etc/varro
umask 077
cat >/etc/varro/dst-column-values.env <<EOF
DST_DOCS_DIR=/agent_data
DST_COLUMN_VALUES_HOST=127.0.0.1
DST_COLUMN_VALUES_PORT=$API_PORT
DST_COLUMN_VALUES_REQUIRE_TOKEN=1
DST_COLUMN_VALUES_TOKEN=$DST_AUTH_TOKEN
EOF

cat >/etc/systemd/system/dst-column-values-api.service <<EOF
[Unit]
Description=Varro DST column-values API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$VARRO_DST_DIR
Environment=PATH=/home/dev/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/etc/varro/dst-column-values.env
ExecStart=$UV_BIN run --project $VARRO_DST_DIR dst-column-values-api
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/caddy/Caddyfile.varro-dst.example <<EOF
www.$DOMAIN {
    redir https://$DOMAIN{uri} permanent
}

$DOMAIN {
    encode zstd gzip
    header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"

    handle_path $API_PREFIX/* {
        reverse_proxy 127.0.0.1:$API_PORT
    }

    respond "Varro DST services" 200
}
EOF

systemctl daemon-reload
systemctl restart postgresql
systemctl enable --now dst-column-values-api.service

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 5432/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

if [[ "${VARRO_REPLACE_CADDYFILE:-0}" == "1" ]]; then
  cp /etc/caddy/Caddyfile "/etc/caddy/Caddyfile.$(date +%Y%m%d%H%M%S).bak"
  cp /etc/caddy/Caddyfile.varro-dst.example /etc/caddy/Caddyfile
  caddy validate --config /etc/caddy/Caddyfile
  systemctl reload caddy
else
  echo "Wrote /etc/caddy/Caddyfile.varro-dst.example"
  echo "To replace the current website Caddyfile, rerun with VARRO_REPLACE_CADDYFILE=1."
fi

echo "PostgreSQL: postgresql+psycopg://$DB_USER:<token>@$DOMAIN:5432/$DB_NAME?sslmode=require"
echo "Column-values API: https://$DOMAIN$API_PREFIX"
