#!/usr/bin/env python3
"""Answer quality smoke: non-empty answers on regression set (W12)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kb_gateway.tools import route_query  # noqa: E402


def main() -> int:
    eval_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "eval/regression_queries.json"
    rows = json.loads(eval_path.read_text())
    passed = failed = 0
    for row in rows:
        qid = row["id"]
        q = row["question"]
        try:
            r = route_query(q, k=3, max_retries=1)
            ans = (r.get("answer") or "").strip()
        except Exception as exc:
            print(f"FAIL {qid} error: {exc}")
            failed += 1
            continue
        if len(ans) < 20:
            print(f"FAIL {qid} empty/short answer ({len(ans)} chars)")
            failed += 1
        else:
            print(f"PASS {qid} len={len(ans)} route={r.get('route')}")
            passed += 1
    print(f"QUALITY SMOKE: {passed} pass, {failed} fail")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
