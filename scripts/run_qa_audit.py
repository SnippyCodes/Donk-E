#!/usr/bin/env python3
"""
scripts/run_qa_audit.py — Standalone CLI Auditor for 18-case E2E Golden QA.

Runs the complete 18-case Golden QA pipeline sequentially through the agent loop,
prints a structured verification table, and exits with status 0 on 100% pass.
"""
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.copilot.agent.qa_audit import run_full_e2e_qa


def main():
    print("=" * 80)
    print("  ASSET INTELLIGENCE COPILOT — 18-CASE E2E GOLDEN QA AUDIT")
    print("=" * 80)
    print("Executing Q1 through Q18 sequentially through full AgentLoop pipeline...\n")

    t0 = time.perf_counter()
    res = run_full_e2e_qa()
    elapsed = round(time.perf_counter() - t0, 2)

    header = f"{'Case':<5} | {'User':<14} | {'Visual Block':<16} | {'Facts':<6} | {'Cite':<6} | {'Vis':<6} | {'State':<6} | {'Latency':<8} | {'Status'}"
    print(header)
    print("-" * len(header))

    for c in res["cases"]:
        cid = c["case_id"]
        user = c["user_id"][:14]
        v_type = c["visual_type"][:16]
        f_mark = "OK" if c["fact_match"] else "FAIL"
        c_mark = "OK" if c["citation_match"] else "FAIL"
        v_mark = "OK" if c["visual_match"] else "FAIL"
        s_mark = "OK" if c["carry_forward_match"] else "FAIL"
        lat = f"{c['latency_ms']}ms"
        stat = c["status"]
        print(f"{cid:<5} | {user:<14} | {v_type:<16} | {f_mark:<6} | {c_mark:<6} | {v_mark:<6} | {s_mark:<6} | {lat:<8} | {stat}")

    print("-" * len(header))
    print(f"\nFinal Result: {res['passed_cases']}/{res['total_cases']} PASS ({res['pass_rate_pct']}%) in {elapsed}s (avg {res['avg_latency_ms']}ms/case)")

    print("\nBugs Caught and Remediated During QA:")
    for b in res["bugs_caught_and_fixed"]:
        print(f"  [{b['bug_id']}] {b['title']} ({b['component']})")
        print(f"         Fix: {b['fix']}")

    if res["passed_cases"] == res["total_cases"]:
        print("\n>>> ALL 18 GOLDEN QA SCENARIOS PASSED 100% END-TO-END! <<<")
        sys.exit(0)
    else:
        print("\n>>> QA AUDIT FAILED! Review errors above. <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
