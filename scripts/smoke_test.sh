#!/usr/bin/env bash
# Smoke test kb-gateway tools (server-only).
set -euo pipefail

cd "$(dirname "$0")/.."
source /srv/org/env/load.sh global 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"

echo "== health =="
"$PY" -c "from kb_gateway.tools import health; import json; print(json.dumps(health(), indent=2))"

echo "== list_namespaces (first 3) =="
"$PY" -c "from kb_gateway.tools import list_namespaces; import json; print(json.dumps(list_namespaces()[:3], indent=2))"

echo "== graph_query stats =="
"$PY" -c "from kb_gateway.tools import graph_query; import json; print(json.dumps(graph_query('stats'), indent=2))"

echo "== route_query (short) =="
"$PY" -c "from kb_gateway.tools import route_query; r=route_query('what is PAS copy structure?', k=3); print('route:', r.get('route')); print('answer:', (r.get('answer') or '')[:200])"

echo "SMOKE OK"
