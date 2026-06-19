#!/usr/bin/env bash
# Regression eval: route_query expected routes (W8 gate sample set).
set -euo pipefail

cd "$(dirname "$0")/.."
source /mnt/blockstorage/env/load.sh global 2>/dev/null || true

PY="${PY:-/root/.venv-langchain-course/bin/python}"
EVAL="${EVAL:-eval/regression_queries.json}"

pass=0
fail=0

while IFS= read -r row; do
  id=$(echo "$row" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
  q=$(echo "$row" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d['question'])")
  exp=$(echo "$row" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d['expected_route'])")
  got=$("$PY" -c "from kb_gateway.tools import route_query; import json; r=route_query('$q', k=3); print(r.get('route',''))" 2>/dev/null | tail -1)
  if [[ "$got" == "$exp" ]]; then
    echo "PASS $id expected=$exp got=$got"
    ((pass++)) || true
  else
    echo "FAIL $id expected=$exp got=$got"
    ((fail++)) || true
  fi
done < <("$PY" -c "import json; [print(json.dumps(x)) for x in json.load(open('$EVAL'))]")

echo "EVAL: $pass pass, $fail fail"
[[ "$fail" -eq 0 ]]
