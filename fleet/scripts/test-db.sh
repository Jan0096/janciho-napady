#!/usr/bin/env bash
# Runs migrations, seed and database tests (RLS, RPC) on a throwaway local Postgres.
# Requires Postgres server binaries (initdb, pg_ctl) – no Docker needed.
set -euo pipefail

cd "$(dirname "$0")/.."
PG_BIN="${PG_BIN:-$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)}"
PATH="$PG_BIN:$PATH"
TMP="$(mktemp -d)"
PORT="${TEST_DB_PORT:-54329}"

cleanup() {
  pg_ctl -D "$TMP/data" -m immediate stop >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

# initdb refuses to run as root; use the postgres OS user when needed.
RUN=()
if [ "$(id -u)" = "0" ]; then
  chown -R postgres "$TMP" 2>/dev/null || true
  RUN=(runuser -u postgres --)
fi

"${RUN[@]}" initdb -D "$TMP/data" -U postgres -A trust >/dev/null
"${RUN[@]}" pg_ctl -D "$TMP/data" -o "-p $PORT -k $TMP -c listen_addresses=''" -l "$TMP/log" -w start >/dev/null

PSQL=(psql -X -q -v ON_ERROR_STOP=1 -h "$TMP" -p "$PORT" -U postgres -d postgres)

"${PSQL[@]}" -f supabase/db-tests/supabase_stub.sql
for f in supabase/migrations/*.sql; do
  echo "migration: $f"
  "${PSQL[@]}" -f "$f"
done
echo "seed: supabase/seed.sql"
"${PSQL[@]}" -f supabase/seed.sql
for f in supabase/db-tests/*_test.sql; do
  echo "test: $f"
  # Query results are discarded; assertions report via NOTICE / ERROR.
  "${PSQL[@]}" -o /dev/null -f "$f" 2>&1 | sed -E 's/^psql:[^ ]+ NOTICE:  /  /'
  [ "${PIPESTATUS[0]}" = "0" ] || exit 1
done
echo "All database tests passed."
