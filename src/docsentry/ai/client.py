import json
import os
from pathlib import Path

import httpx

from docsentry.ai.protocol import EvidenceBundle, ModelAssessment


def _load_env_file() -> None:
    """Loads key-value pairs from .env into os.environ if not already set."""
    for candidate in (Path(".env"), Path("../.env")):
        if candidate.is_file():
            try:
                for line in candidate.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
            except Exception:
                pass


_load_env_file()

SYSTEM_PROMPT = """You are DocSentry's documentation-consistency verifier.
You verify whether a documentation statement remains accurate after a code change.
Use only the evidence provided.

RULES:
1. DRIFT (claim_status: contradicted): Return DRIFT only when doc asserts a concrete factual claim
   that directly contradicts new code behavior (e.g. code returns bytes, doc says returns None;
   or cipher TLS 1.0 removed, doc says TLS 1.0 is permitted by default).
2. POTENTIAL_DRIFT (claim_status: partially_outdated): Return POTENTIAL_DRIFT when a new parameter or
   capability supersedes documented procedural instructions (e.g. native json= added, making manual serialization outdated).
3. NO_DRIFT:
   - claim_status: incomplete_new_capability (New feature added, but existing documented usage remains valid).
   - claim_status: still_accurate (Code change is internal refactoring/optimization; documentation remains factually true).
   - claim_status: historical (Doc describes historical version, changelog, or migration note).
4. UNCERTAIN (claim_status: uncertain): Return UNCERTAIN if evidence is dynamic, incomplete, or ambiguous. Always abstain when in doubt.

Never invent identifiers, line numbers, or facts outside the evidence.
Return valid JSON matching this schema:
{
  "status": "DRIFT | POTENTIAL_DRIFT | NO_DRIFT | UNCERTAIN",
  "claim_status": "contradicted | partially_outdated | incomplete_new_capability | still_accurate | historical | uncertain",
  "severity": "high | medium | low | info",
  "explanation": "One or two concise sentences.",
  "evidence_ids": ["CODE-1", "DOC-1"],
  "reasoning_type": "direct_contradiction | likely_outdated | no_change | insufficient_context",
  "suggested_action": "Actionable advice for the engineer"
}
"""


class ModelClient:
    """HTTP client supporting Ollama and organizer-provided open-weight model endpoints."""

    def __init__(self) -> None:
        self.enabled = (
            os.environ.get("DOCSENTRY_MODEL_ENABLED")
            or os.environ.get("DOCGUARD_MODEL_ENABLED", "true")
        ).lower() == "true"
        self.provider = (
            os.environ.get("DOCSENTRY_MODEL_PROVIDER")
            or os.environ.get("DOCGUARD_MODEL_PROVIDER", "ollama")
        ).lower()
        self.base_url = (
            os.environ.get("DOCSENTRY_MODEL_BASE_URL")
            or os.environ.get("DOCGUARD_MODEL_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.api_key = os.environ.get("DOCSENTRY_MODEL_API_KEY") or os.environ.get(
            "DOCGUARD_MODEL_API_KEY", ""
        )
        self.model_name = os.environ.get("DOCSENTRY_MODEL_NAME") or os.environ.get(
            "DOCGUARD_MODEL_NAME", "qwen3:8b"
        )
        timeout_val = os.environ.get("DOCSENTRY_MODEL_TIMEOUT_SECONDS") or os.environ.get(
            "DOCGUARD_MODEL_TIMEOUT_SECONDS", "60"
        )
        self.timeout = float(timeout_val) if timeout_val.isdigit() else 60.0

    def is_configured(self) -> bool:
        return bool(self.enabled and self.base_url)

    def verify_bundle(self, bundle: EvidenceBundle) -> ModelAssessment:
        if not self.is_configured():
            return ModelAssessment(
                status="UNCERTAIN",
                severity="info",
                explanation=(
                    "Model verifier endpoint not configured; semantic candidate marked UNCERTAIN."
                ),
                evidence_ids=[i.evidence_id for i in bundle.evidence_items[:2]],
                reasoning_type="insufficient_context",
            )

        is_ollama_native = "11434" in self.base_url and not self.base_url.endswith("/v1")

        if is_ollama_native:
            # Native Ollama /api/chat with format: "json"
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": bundle.model_dump_json()},
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0},
            }
        else:
            # OpenAI-compatible /v1/chat/completions
            endpoint = (
                "/chat/completions" if self.base_url.endswith("/v1") else "/v1/chat/completions"
            )
            url = f"{self.base_url}{endpoint}"
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": bundle.model_dump_json()},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code in (401, 403):
                    return ModelAssessment(
                        status="UNCERTAIN",
                        severity="info",
                        explanation=(
                            f"Model authentication failed ({res.status_code}); "
                            "semantic candidate marked UNCERTAIN."
                        ),
                        evidence_ids=[i.evidence_id for i in bundle.evidence_items[:2]],
                        reasoning_type="insufficient_context",
                    )
                res.raise_for_status()
                data = res.json()

                raw_content = ""
                if "message" in data and "content" in data["message"]:
                    # Native Ollama response
                    raw_content = data["message"]["content"]
                elif "choices" in data and data["choices"]:
                    # OpenAI-compatible response
                    raw_content = data["choices"][0]["message"]["content"]
                elif "response" in data:
                    raw_content = data["response"]
                else:
                    raw_content = str(data)

                # Parse JSON block
                clean_json = raw_content.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[1]
                    if clean_json.endswith("```"):
                        clean_json = clean_json.rsplit("\n", 1)[0]

                parsed = json.loads(clean_json)
                if isinstance(parsed, dict) and "claim_status" not in parsed:
                    status = parsed.get("status")
                    if status == "DRIFT":
                        parsed["claim_status"] = "contradicted"
                    elif status == "POTENTIAL_DRIFT":
                        parsed["claim_status"] = "partially_outdated"
                    elif status == "NO_DRIFT":
                        parsed["claim_status"] = "still_accurate"
                    else:
                        parsed["claim_status"] = "uncertain"
                return ModelAssessment.model_validate(parsed)

        except Exception as exc:
            return ModelAssessment(
                status="UNCERTAIN",
                severity="info",
                explanation=f"Model verification failed ({type(exc).__name__}); marked UNCERTAIN.",
                evidence_ids=[i.evidence_id for i in bundle.evidence_items[:2]],
                reasoning_type="insufficient_context",
            )
