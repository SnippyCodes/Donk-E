"""
backend/tests/test_e2e_qa.py — Pytest suite verifying 18/18 Golden QA scenarios end-to-end.

Covers:
1. Fact Invariant & Zero-LLM-Math verification across Q1–Q18
2. Citation Grounding verification
3. Visual Contract verification
4. Stateful Multi-User Carry-Forward verification (Q11->Q16, Q12->Q2->Q15, Q13->Q15, Q14, Q17, Q18)
"""
import pytest
from backend.copilot.agent.qa_audit import run_full_e2e_qa


@pytest.fixture(scope="module")
def audit_results():
    """Run full E2E QA audit suite across all 18 golden scenarios."""
    return run_full_e2e_qa()


def test_e2e_qa_overall_pass_rate(audit_results):
    """Assert all 18 golden cases pass 100% end-to-end with 0 failures."""
    assert audit_results["total_cases"] == 18
    assert audit_results["passed_cases"] == 18, (
        f"Failed cases: {[c['case_id'] for c in audit_results['cases'] if c['status'] != 'PASS']}"
    )
    assert audit_results["pass_rate_pct"] == 100.0


@pytest.mark.parametrize("idx", list(range(18)))
def test_individual_golden_case(audit_results, idx):
    """Verify each individual case satisfies facts, citations, visuals, and has 0 token leaks or tool errors."""
    c = audit_results["cases"][idx]
    case_id = c["case_id"]
    assert c["status"] == "PASS", f"Case {case_id} failed: errors={c.get('errors')}"
    assert c["fact_match"] is True, f"Case {case_id} failed fact invariant match"
    assert c["citation_match"] is True, f"Case {case_id} failed citation grounding match"
    assert c["visual_match"] is True, f"Case {case_id} failed visual contract match"
    assert c["carry_forward_match"] is True, f"Case {case_id} failed stateful carry-forward match"
    assert not c["errors"], f"Case {case_id} leaked tool errors or raw tokens: {c['errors']}"
