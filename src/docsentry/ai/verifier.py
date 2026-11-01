import re
from typing import Sequence

from docsentry.ai.client import ModelClient
from docsentry.ai.protocol import EvidenceBundle, EvidenceItem
from docsentry.contracts.code import CodeFact
from docsentry.contracts.docs import CandidateLink, DocSpan
from docsentry.contracts.findings import EvidenceRef, Finding


class SemanticModelVerifier:
    """Bounded AI-assisted verifier for behavioral documentation drift."""

    def __init__(self, client: ModelClient | None = None) -> None:
        self.client = client or ModelClient()

    def verify_candidates(
        self,
        facts: Sequence[CodeFact],
        spans: Sequence[DocSpan],
        candidates: Sequence[CandidateLink],
        covered_doc_spans: set[tuple[str, int]],
    ) -> list[Finding]:
        fact_map = {f.fact_id: f for f in facts}
        span_map = {s.span_id: s for s in spans}

        semantic_findings: list[Finding] = []

        # Find candidates not covered by deterministic rules
        for link in candidates:
            fact = fact_map.get(link.code_fact_id)
            span = span_map.get(link.doc_span_id)
            if not fact or not span:
                continue

            # Skip spans already diagnosed by deterministic rules
            if (span.path, span.line_start) in covered_doc_spans:
                continue

            # Intelligent routing: filter out non-actionable or negative control combinations
            span_claim = getattr(span, "claim_type", "active_assertion")
            if span_claim == "historical_migration":
                continue

            if span_claim == "code_example" and fact.kind == "default_changed":
                continue

            # Sibling disambiguation: do not attribute to fact if doc is for sibling
            siblings = fact.metadata.get("sibling_symbols", [])
            if siblings and isinstance(siblings, list) and fact.symbol:
                has_sym = (
                    fact.symbol in span.inline_code
                    or re.search(rf"\b{re.escape(fact.symbol)}\b", span.text)
                    or any(fact.symbol in h for h in span.heading_path)
                    or fact.symbol in span.path
                )
                if not has_sym:
                    has_sibling = any(
                        sib in span.inline_code
                        or re.search(rf"\b{re.escape(str(sib))}\b", span.text)
                        or any(str(sib) in h for h in span.heading_path)
                        or str(sib) in span.path
                        for sib in siblings
                    )
                    if has_sibling:
                        continue

            # Only invoke model if:
            # 1. Fact is behavioral (return_changed, exception_changed, behavior_changed)
            # 2. OR Candidate link is strong semantic match and span is an active/procedural claim
            is_behavioral = getattr(fact, "category", "syntactic") == "behavioral"
            is_strong_semantic = link.score >= 5.0 and span_claim in (
                "active_assertion",
                "procedural_instruction",
                "api_reference",
                "configuration_instruction",
            )

            if not (is_behavioral or is_strong_semantic):
                continue

            # Only verify behavioral or signature changes not already flagged
            rule_id = "PY-BEHAVIOR-006"

            # Construct bounded evidence items
            code_summary = (
                f"{fact.kind}: {fact.member or fact.symbol} "
                f"(before={fact.before}, after={fact.after})"
            )
            code_ev = EvidenceItem(
                evidence_id="CODE-1",
                role="code",
                path=fact.path,
                line_start=fact.line_after or fact.line_before or 1,
                line_end=fact.line_after or fact.line_before or 1,
                quote=code_summary,
                source_kind="ast_fact",
            )
            doc_ev = EvidenceItem(
                evidence_id="DOC-1",
                role="documentation",
                path=span.path,
                line_start=span.line_start,
                line_end=span.line_end,
                quote=span.raw_text,
                source_kind="doc_span",
            )

            bundle = EvidenceBundle(
                bundle_id=f"bundle-{fact.fact_id}-{span.span_id}",
                code_fact_id=fact.fact_id,
                code_fact_summary=f"{fact.kind} on {fact.symbol or fact.path}",
                code_path=fact.path,
                code_before=fact.before,
                code_after=fact.after,
                claim_type=span_claim,
                heading_context=" > ".join(span.heading_path),
                evidence_items=[code_ev, doc_ev],
            )

            assessment = self.client.verify_bundle(bundle)

            if assessment.status in ("DRIFT", "POTENTIAL_DRIFT", "UNCERTAIN"):
                finding_id = f"DG-AI-{len(semantic_findings) + 1:03d}"
                f_evidence = [
                    EvidenceRef(
                        evidence_id="E1",
                        role="code",
                        path=code_ev.path,
                        line_start=code_ev.line_start,
                        line_end=code_ev.line_end,
                        quote=code_ev.quote,
                        source_kind="ast_fact",
                    ),
                    EvidenceRef(
                        evidence_id="E2",
                        role="documentation",
                        path=doc_ev.path,
                        line_start=doc_ev.line_start,
                        line_end=doc_ev.line_end,
                        quote=doc_ev.quote,
                        source_kind="doc_span",
                    ),
                ]

                target_name = fact.symbol or fact.path
                semantic_findings.append(
                    Finding(
                        finding_id=finding_id,
                        status=assessment.status,
                        severity=assessment.severity,
                        rule_id=rule_id,
                        category="behavioral_drift",
                        title=f"Behavioral change in '{target_name}' may affect documentation",
                        explanation=assessment.explanation,
                        evidence=f_evidence,
                        confidence=0.75 if assessment.status == "POTENTIAL_DRIFT" else None,
                        verification="model_assisted",
                        suggested_action=assessment.suggested_action,
                    )
                )

        return semantic_findings
