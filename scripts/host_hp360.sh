#!/usr/bin/env bash
# Private HP360 demo runner. Never binds to 0.0.0.0 or any public IP.
set -euo pipefail

BIND_IP="${PLACEMENT_BIND_IP:-127.0.0.1}"
PORT="${PLACEMENT_PORT:-5088}"

python3 - "$BIND_IP" "$PORT" <<'PY'
import ipaddress
import sys

try:
    address=ipaddress.ip_address(sys.argv[1])
    port=int(sys.argv[2])
    assert 1024 <= port <= 65535
    assert address.is_loopback or (
        address.version == 4 and address in ipaddress.ip_network("100.64.0.0/10")
    )
except (ValueError, AssertionError):
    sys.exit("Refusing unsafe bind address/port. Use loopback or your private Tailscale IP (100.64.0.0/10) and port 1024-65535.")
PY

if [[ -z "${SECRET_KEY:-}" ]]; then
  export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
fi

if command -v gunicorn >/dev/null 2>&1; then
  GUNICORN="$(command -v gunicorn)"
elif [[ -x ".venv/bin/gunicorn" ]]; then
  GUNICORN=".venv/bin/gunicorn"
else
  echo "Missing gunicorn. Install: pip install -r requirements-hp360.txt" >&2
  exit 1
fi

echo "Private campus placement preview: http://${BIND_IP}:${PORT}/analytics"
echo "Oracle is optional for the explicitly marked synthetic UI preview."
if [[ "$BIND_IP" == "127.0.0.1" ]]; then
  exec "$GUNICORN" --workers 2 --threads 4 --timeout 20 --bind "127.0.0.1:${PORT}" app:app
else
  exec "$GUNICORN" --workers 2 --threads 4 --timeout 20 \
    --bind "127.0.0.1:${PORT}" --bind "${BIND_IP}:${PORT}" app:app
fi
