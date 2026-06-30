#!/usr/bin/env python3
"""Regression checks for the James learning-KB retrieval contract.

This complements route evals. It protects the high-risk behavior where a broad
course-heavy query can answer "no context" unless the local wrapper or MCP
query_all/targeted namespaces are used.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "eval/retrieval_contract_cases.json"
WRAPPER = Path("/root/.claude/skills/_shared/learning-kb-query.sh")


def run_wrapper(question: str, graph: bool = False, timeout: int = 90) -> tuple[int, str]:
    cmd = [str(WRAPPER)]
    if graph:
        cmd.append("--graph")
    cmd.append(question)
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout


def check_case(row: dict, output: str, rc: int) -> list[str]:
    failures: list[str] = []
    if rc != 0:
        failures.append(f"command exited {rc}")
    lowered = output.lower()
    for phrase in row.get("forbidden_phrases", []):
        if phrase.lower() in lowered:
            failures.append(f"forbidden phrase present: {phrase}")
    expected_any = row.get("expected_sources_any", [])
    if expected_any and not any(term.lower() in lowered for term in expected_any):
        failures.append("none of expected source terms found: " + ", ".join(expected_any))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--limit", type=int, default=5, help="default keeps smoke fast")
    parser.add_argument("--all", action="store_true", help="run all 20 cases")
    parser.add_argument("--id", action="append", dest="ids", help="run one or more case ids")
    args = parser.parse_args()

    rows = json.loads(args.cases.read_text())
    executable_rows = [
        row for row in rows
        if row["surface"] in {"local-wrapper", "graph-required", "namespace-or-query_all", "targeted", "local-wrapper-first"}
    ]
    if args.ids:
        selected = [row for row in rows if row["id"] in set(args.ids)]
    elif args.all:
        selected = executable_rows
    else:
        selected = executable_rows[: args.limit]

    if not WRAPPER.exists():
        print(f"FAIL wrapper missing: {WRAPPER}")
        return 1

    passed = failed = 0
    for row in selected:
        graph = row["surface"] == "graph-required"
        try:
            rc, out = run_wrapper(row["input_text"], graph=graph)
        except subprocess.TimeoutExpired:
            print(f"FAIL {row['id']} timeout")
            failed += 1
            continue
        failures = check_case(row, out, rc)
        if failures:
            print(f"FAIL {row['id']}: {'; '.join(failures)}")
            failed += 1
        else:
            print(f"PASS {row['id']} expected={row['expected_tools']}")
            passed += 1

    skipped = len(rows) - len(selected)
    print(f"RETRIEVAL CONTRACT: {passed} pass, {failed} fail, {skipped} not run")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
