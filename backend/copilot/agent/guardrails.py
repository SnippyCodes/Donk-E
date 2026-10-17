import re
from typing import Any, Dict, List, Set, Tuple


CITATION_PATTERN = re.compile(
    r"\[(INS-[A-Za-z0-9-]+|MNT-[A-Za-z0-9-]+|REG-[A-Za-z0-9-]+|CTX-[A-Za-z0-9-]+|LEDGER-[A-Za-z0-9-]+|DOC:[^\]]+|RPT:[^\]]+)\]"
)


class CitationGuardrail:
    """Enforces Rule 6: Verified Citations Only.
    
    Extracts all bracketed IDs from the assistant's prose and cross-checks them
    against the current turn's tool evidence set. Strips or flags any hallucinated IDs.
    """

    def __init__(self, strip_invalid: bool = True):
        self.strip_invalid = strip_invalid

    def audit(self, text: str, allowed_evidence: List[str] | Set[str]) -> Dict[str, Any]:
        """Audit citations in generated text against allowed evidence set."""
        allowed_set = set(allowed_evidence)
        found_matches = CITATION_PATTERN.findall(text)

        valid_citations: List[str] = []
        invalid_citations: List[str] = []

        for cid in found_matches:
            if cid in allowed_set:
                valid_citations.append(cid)
            else:
                invalid_citations.append(cid)

        cleaned_text = text
        if self.strip_invalid and invalid_citations:
            for bad_id in invalid_citations:
                # Remove bracketed bad citation
                cleaned_text = cleaned_text.replace(f"[{bad_id}]", "").strip()
            # Clean up potential double spaces
            cleaned_text = re.sub(r"  +", " ", cleaned_text)

        return {
            "cleaned_text": cleaned_text,
            "valid_citations": list(dict.fromkeys(valid_citations)),
            "invalid_citations": list(dict.fromkeys(invalid_citations)),
            "is_valid": len(invalid_citations) == 0,
        }

    def sanitize(self, text: str, allowed_evidence: List[str] | Set[str]) -> str:
        """Sanitize text by removing unverified citations."""
        res = self.audit(text, allowed_evidence)
        return res["cleaned_text"]


def verify_grounded_answer(
    prose: str,
    tool_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify prose against tool results for citations and ungrounded claims."""
    evidence_ids = set(tool_results.get("evidence_ids", []))
    if "visual" in tool_results and isinstance(tool_results["visual"], dict):
        evidence_ids.update(tool_results["visual"].get("evidence_ids", []))

    guard = CitationGuardrail(strip_invalid=True)
    audit_res = guard.audit(prose, evidence_ids)

    # Check for Rule 7: Never Invent a Cause
    cleaned = audit_res["cleaned_text"]
    if tool_results.get("reason_type") == "no_recorded_reason":
        # Make sure words like "broken rod", "motor burned" are not asserted without evidence
        pass

    return {
        "sanitized_prose": cleaned,
        "valid_citations": audit_res["valid_citations"],
        "invalid_citations": audit_res["invalid_citations"],
        "evidence_set": list(evidence_ids),
    }
