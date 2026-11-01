from typing import Sequence

from docsentry.contracts.code import CodeFact
from docsentry.contracts.docs import CandidateLink, DocSpan
from docsentry.contracts.findings import Finding
from docsentry.rules.config_flags import detect_config_flag_drift
from docsentry.rules.constants import detect_constant_drift
from docsentry.rules.defaults import detect_default_drift
from docsentry.rules.returns import detect_return_drift
from docsentry.rules.signatures import detect_signature_drift
from docsentry.rules.symbols import detect_symbol_drift


class DeterministicRuleEngine:
    """Evaluates candidate code-to-documentation pairs using deterministic rules."""

    def evaluate(
        self,
        facts: Sequence[CodeFact],
        spans: Sequence[DocSpan],
        candidates: Sequence[CandidateLink],
    ) -> list[Finding]:
        fact_map = {f.fact_id: f for f in facts}
        span_map = {s.span_id: s for s in spans}

        findings: list[Finding] = []
        seen_keys: set[tuple[str, str, str]] = set()

        for link in candidates:
            fact = fact_map.get(link.code_fact_id)
            span = span_map.get(link.doc_span_id)
            if not fact or not span:
                continue

            # Candidate finding ID
            finding_id = f"DG-{len(findings) + 1:04d}"

            # PY-DEFAULT-001
            f_default = detect_default_drift(fact, span, finding_id)
            if f_default:
                key = (f_default.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_default)
                    continue

            # PY-PARAM-002
            f_param = detect_signature_drift(fact, span, finding_id)
            if f_param:
                key = (f_param.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_param)
                    continue

            # PY-SYMBOL-003
            f_sym = detect_symbol_drift(fact, span, finding_id)
            if f_sym:
                key = (f_sym.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_sym)
                    continue

            # PY-CONFIG-004
            f_cfg = detect_config_flag_drift(fact, span, finding_id)
            if f_cfg:
                key = (f_cfg.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_cfg)
                    continue

            # PY-CONST-005
            f_const = detect_constant_drift(fact, span, finding_id)
            if f_const:
                key = (f_const.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_const)
                    continue

            # PY-RETURN-007
            f_ret = detect_return_drift(fact, span, finding_id)
            if f_ret:
                key = (f_ret.rule_id, fact.fact_id, span.span_id)
                if key not in seen_keys:
                    seen_keys.add(key)
                    findings.append(f_ret)
                    continue

        return findings
