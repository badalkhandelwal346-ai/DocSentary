import re

from docsentry.contracts.code import CodeFact
from docsentry.contracts.docs import DocSpan
from docsentry.contracts.findings import EvidenceRef, Finding


def detect_return_drift(
    code_fact: CodeFact,
    doc_span: DocSpan,
    finding_id: str,
) -> Finding | None:
    """
    PY-RETURN-007: Return Value / Contract Drift.
    Triggers when a function's return expressions change, and documentation asserts
    the previous return value.
    """
    if code_fact.kind != "return_changed":
        return None

    span_text = doc_span.text
    span_lower = span_text.lower()

    # Must mention return or returns
    if not any(w in span_lower for w in ["return", "returns", "empty"]):
        return None

    func_name = code_fact.symbol or ""
    # Doc must mention the function or be under a heading with the function
    mentions_func = bool(
        func_name in doc_span.inline_code
        or re.search(rf"\b{re.escape(func_name)}\b", span_text)
        or any(func_name in h for h in doc_span.heading_path)
    )
    if not mentions_func:
        return None

    old_ret = str(code_fact.before).strip() if code_fact.before else ""
    new_ret = str(code_fact.after).strip() if code_fact.after else ""

    # Check if doc asserts the old return value
    # e.g. "returns None", "returns []", "returns (result, errors)"
    mentions_old = bool(
        old_ret
        and (
            old_ret.lower() in span_lower
            or (old_ret == "None" and "none" in span_lower)
            or (old_ret == "b''" and ("bytes" in span_lower or "empty byte" in span_lower))
        )
    )
    # Check if doc already mentions the new return value
    mentions_new = bool(
        new_ret and (new_ret.lower() in span_lower or (new_ret == "b''" and "b''" in span_text))
    )

    if not mentions_old or mentions_new:
        return None

    return Finding(
        finding_id=finding_id,
        status="DRIFT",
        severity="high",
        rule_id="PY-RETURN-007",
        category="return_contract_mismatch",
        title=f"Documented return value for '{func_name}' is outdated",
        explanation=(
            f"Function '{func_name}' return contract changed from '{old_ret}' to '{new_ret}' in "
            f"{code_fact.path}, but documentation still claims it returns '{old_ret}'."
        ),
        evidence=[
            EvidenceRef(
                evidence_id="E1",
                role="code",
                path=code_fact.path,
                line_start=code_fact.line_after or code_fact.line_before or 1,
                line_end=code_fact.line_after or code_fact.line_before or 1,
                quote=f"return: changed from {old_ret} to {new_ret}",
                source_kind="ast_fact",
            ),
            EvidenceRef(
                evidence_id="E2",
                role="documentation",
                path=doc_span.path,
                line_start=doc_span.line_start,
                line_end=doc_span.line_end,
                quote=doc_span.raw_text,
                source_kind="doc_span",
            ),
        ],
        confidence=1.0,
        verification="deterministic",
        suggested_action=(
            f"Update '{doc_span.path}:{doc_span.line_start}' to reflect return value '{new_ret}'."
        ),
    )
