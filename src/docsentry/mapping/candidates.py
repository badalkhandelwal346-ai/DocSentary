import re
from typing import Sequence

from docsentry.contracts.code import CodeFact
from docsentry.contracts.docs import CandidateLink, DocSpan


def tokenize_identifier(name: str) -> set[str]:
    """Splits snake_case and camelCase into lowercased tokens."""
    tokens = re.split(r"[_.\-/\\]+", name)
    out: set[str] = set()
    for t in tokens:
        # Split camel case
        sub = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", t)
        for s in sub:
            out.add(s.lower())
    return out


class CandidateMapper:
    """Ranks documentation spans for each changed code fact using weighted relevance scoring."""

    def __init__(self, top_k: int = 5, min_score: float = 4.0) -> None:
        self.top_k = top_k
        self.min_score = min_score

    def map(
        self,
        facts: Sequence[CodeFact],
        spans: Sequence[DocSpan],
    ) -> list[CandidateLink]:
        links: list[CandidateLink] = []

        for fact in facts:
            scored_spans: list[tuple[float, list[str], DocSpan]] = []

            fact_symbol = fact.symbol or ""
            fact_qname = fact.qualified_name or fact_symbol
            fact_member = fact.member or ""
            fact_path = fact.path
            fact_tokens = tokenize_identifier(fact_symbol) | tokenize_identifier(fact_member)

            linked_params = fact.metadata.get("linked_params", [])
            if isinstance(linked_params, list):
                for lp in linked_params:
                    fact_tokens |= tokenize_identifier(str(lp))

            for span in spans:
                score = 0.0
                reasons: list[str] = []
                span_text = span.text

                # 1. Exact qualified symbol match
                if fact_qname and fact_qname in span_text:
                    score += 10.0
                    reasons.append("exact_qualified_symbol_match")

                # 2. Exact unqualified symbol match
                elif fact_symbol and (
                    fact_symbol in span.inline_code
                    or re.search(rf"\b{re.escape(fact_symbol)}\b", span_text)
                ):
                    score += 8.0
                    reasons.append("exact_unqualified_symbol_match")

                # 3. Exact parameter or flag match
                params_to_check = [fact_member] if fact_member else []
                if isinstance(linked_params, list):
                    params_to_check.extend([str(p) for p in linked_params])

                for p_check in params_to_check:
                    if p_check and (
                        p_check in span.inline_code
                        or re.search(rf"\b{re.escape(p_check)}\b", span_text)
                    ):
                        score += 6.0
                        reasons.append("exact_parameter_or_flag_match")
                        break

                # 4. Source path link match
                for link in span.links:
                    if fact_path in link or Path_matches(fact_path, link):
                        score += 5.0
                        reasons.append("source_path_link_match")
                        break

                # 5. Heading keyword match
                for heading in span.heading_path:
                    heading_tokens = tokenize_identifier(heading)
                    if fact_tokens & heading_tokens:
                        score += 3.0
                        reasons.append("heading_keyword_match")
                        break

                # 6. Code fence signature match
                if span.block_type == "fence":
                    if fact_symbol and fact_symbol in span_text:
                        score += 2.0
                        reasons.append("code_fence_signature_match")

                # 7. Value match (if old value appears near member)
                if fact.before and fact.before != "None":
                    if re.search(rf"\b{re.escape(str(fact.before))}\b", span_text):
                        score += 1.0
                        reasons.append("related_constant_or_value_match")

                # 8. Behavioral semantic keyword match
                span_lower = span_text.lower()
                if fact.kind == "return_changed" and any(
                    w in span_lower for w in ["return", "returns", "empty", "result"]
                ):
                    score += 6.0
                    reasons.append("return_semantic_match")
                elif fact.kind == "exception_changed" and any(
                    w in span_lower for w in ["raise", "raises", "exception", "error"]
                ):
                    score += 6.0
                    reasons.append("exception_semantic_match")
                elif fact.kind == "behavior_changed" and any(
                    w in span_lower for w in ["auth", "login", "async", "await", "sync"]
                ):
                    score += 5.0
                    reasons.append("behavior_semantic_match")

                # 9. Call-site and linked parameter propagation
                if linked_params:
                    span_tokens = set(re.findall(r"[a-z0-9]+", span_lower))
                    for lp in linked_params:
                        lp_tokens = tokenize_identifier(str(lp))
                        if (lp_tokens & span_tokens) and (
                            fact.kind in ("constant_changed", "default_changed")
                        ):
                            score += 4.0
                            reasons.append("call_site_linked_match")
                            break

                # 10. Claim-type relevance adjustment
                span_claim = getattr(span, "claim_type", "active_assertion")
                if span_claim == "historical_migration":
                    # Historical/changelog entries are low relevance for current drift
                    score = max(0.0, score - 6.0)
                elif span_claim == "code_example" and fact.kind == "default_changed":
                    # Code examples with explicit arguments do not assert defaults
                    score = max(0.0, score - 5.0)
                elif span_claim == "procedural_instruction":
                    if fact.kind == "parameter_added" and (
                        fact_tokens & set(re.findall(r"[a-z0-9]+", span_lower))
                    ):
                        score += 5.0
                        reasons.append("procedural_instruction_match")
                elif span_claim == "api_reference":
                    if fact.symbol and fact.symbol in span_text:
                        score += 3.0
                        reasons.append("api_reference_match")
                elif span_claim == "configuration_instruction":
                    if fact.kind in ("config_flag_changed", "constant_changed"):
                        score += 4.0
                        reasons.append("configuration_instruction_match")

                # 11. Sibling disambiguation penalty
                siblings = fact.metadata.get("sibling_symbols", [])
                sibling_consts = fact.metadata.get("sibling_constants", [])
                all_sibs = (siblings if isinstance(siblings, list) else []) + (
                    sibling_consts if isinstance(sibling_consts, list) else []
                )
                if all_sibs and fact.symbol:
                    has_this_symbol = (
                        fact.symbol in span.inline_code
                        or re.search(rf"\b{re.escape(fact.symbol)}\b", span_text)
                    )
                    if not has_this_symbol:
                        for sib in all_sibs:
                            sib_str = str(sib)
                            if sib_str and (
                                sib_str in span.inline_code
                                or re.search(rf"\b{re.escape(sib_str)}\b", span_text)
                            ):
                                score = max(0.0, score - 6.0)
                                break

                if score >= self.min_score:
                    scored_spans.append((score, reasons, span))

            # Sort descending by score
            scored_spans.sort(key=lambda x: x[0], reverse=True)

            # Keep top K
            for rank, (score, reasons, span) in enumerate(scored_spans[: self.top_k], start=1):
                links.append(
                    CandidateLink(
                        code_fact_id=fact.fact_id,
                        doc_span_id=span.span_id,
                        score=score,
                        match_reasons=reasons,
                        rank=rank,
                    )
                )

        return links


def Path_matches(source_path: str, link_path: str) -> bool:
    """Helper to check if link references source file."""
    src_clean = source_path.replace("\\", "/").strip("/")
    lnk_clean = link_path.replace("\\", "/").strip("/")
    return src_clean.endswith(lnk_clean) or lnk_clean.endswith(src_clean)
