"""Fail-closed public-safety scrubber for exported mock artifacts."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .types import CSV_LIVE_RUN_BANNER, CSV_MOCK_ONLY_BANNER, LIVE_RUN_BANNER, MOCK_ONLY_BANNER, ScrubFinding, ScrubResult


HASH_VALUE_KEYS = frozenset(
    {
        "scenario_card_hash",
        "prompt_template_hash",
        "raw_output_sha256",
        "sha256_of_match_prefix",
    }
)

HTTP_SCHEME_RE = "http" + "s?://"
LOCAL_URL_RE = "http" + "s?://(?:local" + "host|127[.]0[.]0[.]1|0[.]0[.]0[.]0|\\[::1\\])[^\\s)]*"
POSIX_ROOTS_RE = "^/(?:ho" + "me|Users|root|var|tmp)/|~/"

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----", re.MULTILINE)),
    ("AUTH_HEADER", re.compile(r"\bAuthorization:\s*Bearer\s+\S+|\bCookie:\s*\S+", re.IGNORECASE | re.MULTILINE)),
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Z0-9._%+-]+\s*(?:@|\[at\])\s*[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE | re.MULTILINE)),
    ("PHONE_SHAPE", re.compile(r"(?:\+?1[\s.-]?)?(?:\([0-9]{3}\)|[0-9]{3})[\s.-][0-9]{3}[\s.-][0-9]{4}", re.MULTILINE)),
    ("LOCAL_PATH", re.compile(POSIX_ROOTS_RE + r"|[A-Z]:\\", re.MULTILINE)),
    ("LOCAL_URL", re.compile(LOCAL_URL_RE, re.IGNORECASE | re.MULTILINE)),
    ("HTTP_URL", re.compile(HTTP_SCHEME_RE + r"[^\s)\]]+", re.IGNORECASE | re.MULTILINE)),
    ("SLACK_ID_SHAPE", re.compile(r"\b[UCT](?=[A-Z0-9]{8,}\b)(?=[A-Z0-9]*[0-9])[A-Z0-9]{8,}\b", re.MULTILINE)),
    ("AWS_KEY_SHAPE", re.compile(r"\bAKIA[0-9A-Z]{16}\b|\bA\[K\]IA[A-Z0-9.]{6,}\b", re.MULTILINE)),
    ("GITHUB_TOKEN_SHAPE", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b", re.MULTILINE)),
    ("OPENAI_KEY_SHAPE", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b", re.MULTILINE)),
    ("ANTHROPIC_KEY_SHAPE", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", re.MULTILINE)),
    ("GOOGLE_KEY_SHAPE", re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b", re.MULTILINE)),
    ("PROVIDER_REQUEST_ID", re.compile(r"\b(?:req|chatcmpl|msg|genai|run)_[A-Za-z0-9_-]{12,}\b", re.IGNORECASE | re.MULTILINE)),
    ("RAW_EXCEPTION_TRACE", re.compile(r"Traceback \(most recent call last\):|\b(?:File \"/.+\", line \d+|Exception:|RuntimeError:)", re.MULTILINE)),
    ("RAW_PROMPT_OR_RESPONSE_DUMP", re.compile(r"\b(?:raw_prompt|raw_request|raw_response|response_body|request_body)\b", re.IGNORECASE | re.MULTILINE)),
    ("GENERIC_TOKEN_SHAPE", re.compile(r"\b(?:api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9_./+=-]{20,}\b", re.IGNORECASE | re.MULTILINE)),
    ("LONG_BASE64_OR_HEX", re.compile(r"\b(?:[A-Fa-f0-9]{64,}|[A-Za-z0-9+/=]{80,})\b", re.MULTILINE)),
    ("MARKDOWN_BEACON", re.compile(r"!?\[[^\]]*\]\(" + HTTP_SCHEME_RE + r"[^)]+\)", re.IGNORECASE | re.MULTILINE)),
    ("REAL_LOOKING_RECORD_ID", re.compile(r"\b(?:case|voucher|receipt|claim|payment|ticket)[-_ ]?(?=[A-Z0-9]{6,}\b)(?=[A-Z0-9]*[0-9])[A-Z0-9]{6,}\b", re.IGNORECASE | re.MULTILINE)),
    ("OFFICIAL_ACTION_WORDING", re.compile(r"\b(?:performed official action|approved for payment|real claimant|real payment|production deployment|external system effect)\b", re.IGNORECASE | re.MULTILINE)),
)


def scan_paths(paths: list[Path]) -> ScrubResult:
    findings: list[ScrubFinding] = []
    checked: list[str] = []
    for path in sorted(paths):
        if path.is_dir():
            continue
        text = path.read_text(encoding="utf-8")
        checked.append(_portable_path(path))
        findings.extend(scan_artifact_text(_portable_path(path), text, path.suffix))
    status = "blocked" if findings else "passed"
    return ScrubResult(status=status, findings=tuple(findings), checked_artifacts=tuple(checked))


def scan_artifact_text(artifact_path: str, text: str, suffix: str = "") -> tuple[ScrubFinding, ...]:
    findings: list[ScrubFinding] = []
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if suffix == ".json" or artifact_path.endswith(".json"):
        findings.extend(_json_banner_findings(artifact_path, text))
        scan_text = _json_text_for_scan(text)
    elif suffix == ".csv" or artifact_path.endswith(".csv"):
        expected = CSV_LIVE_RUN_BANNER if _is_live_artifact(artifact_path, text) else CSV_MOCK_ONLY_BANNER
        if first_line != expected:
            findings.append(_finding("MISSING_OR_ALTERED_BANNER", artifact_path, text, 0))
        scan_text = text
    else:
        expected = LIVE_RUN_BANNER if _is_live_artifact(artifact_path, text) else MOCK_ONLY_BANNER
        if first_line != expected:
            findings.append(_finding("MISSING_OR_ALTERED_BANNER", artifact_path, text, 0))
        scan_text = text

    for finding_class, pattern in PATTERNS:
        for match in pattern.finditer(scan_text):
            if finding_class == "OFFICIAL_ACTION_WORDING" and _line_is_negated(scan_text, match.start()):
                continue
            findings.append(_finding(finding_class, artifact_path, match.group(0), match.start()))
    return tuple(findings)


def write_scrub_report(path: Path, result: ScrubResult, artifact_mode: str = "mock") -> None:
    banner = LIVE_RUN_BANNER if artifact_mode == "live" else MOCK_ONLY_BANNER
    lines = [
        banner,
        "",
        "# Scrub Report",
        "",
        "Synthetic notice: mock-only bundle; no real systems, records, or actions.",
        f"scrubber_status: {result.status}",
        f"publication_gate: {'passed' if result.passed else 'blocked'}",
        "",
        "## Checked Artifacts",
    ]
    for artifact in result.checked_artifacts:
        lines.append(f"- {artifact}")
    lines.extend(["", "## Findings"])
    if not result.findings:
        lines.append("- none")
    else:
        for finding in result.findings:
            payload = asdict(finding)
            lines.append(
                "- class={finding_class}; count={count}; sha256_of_match_prefix={sha256_of_match_prefix}; artifact_path={artifact_path}; byte_offset={byte_offset}".format(
                    **payload
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _json_banner_findings(artifact_path: str, text: str) -> list[ScrubFinding]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return [_finding("INVALID_JSON", artifact_path, text, 0)]
    if not isinstance(payload, dict):
        return [_finding("JSON_TOP_LEVEL_NOT_OBJECT", artifact_path, text, 0)]
    keys = list(payload.keys())
    if not keys:
        return [_finding("MISSING_OR_ALTERED_BANNER", artifact_path, text, 0)]
    if _is_live_artifact(artifact_path, text):
        if keys[0] != "_live_run_notice" or payload.get("_live_run_notice") != LIVE_RUN_BANNER:
            return [_finding("MISSING_OR_ALTERED_BANNER", artifact_path, text, 0)]
    elif keys[0] != "_mock_only_notice" or payload.get("_mock_only_notice") != MOCK_ONLY_BANNER:
        return [_finding("MISSING_OR_ALTERED_BANNER", artifact_path, text, 0)]
    return []


def _is_live_artifact(artifact_path: str, text: str) -> bool:
    return "live_" in artifact_path or text.startswith(LIVE_RUN_BANNER) or text.startswith(CSV_LIVE_RUN_BANNER) or '"_live_run_notice"' in text


def _json_text_for_scan(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    scrubbed = _drop_hash_values(payload, parent_key="")
    return json.dumps(scrubbed, sort_keys=True, ensure_ascii=False)


def _drop_hash_values(value: Any, parent_key: str) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_hash_values(item, key)
            for key, item in value.items()
            if key not in HASH_VALUE_KEYS and not key.endswith("_hash")
        }
    if isinstance(value, list):
        return [_drop_hash_values(item, parent_key) for item in value]
    return value


def _finding(finding_class: str, artifact_path: str, matched_text: str, byte_offset: int) -> ScrubFinding:
    prefix = matched_text[:64].encode("utf-8", errors="replace")
    return ScrubFinding(
        finding_class=finding_class,
        count=1,
        sha256_of_match_prefix=hashlib.sha256(prefix).hexdigest()[:16],
        artifact_path=artifact_path,
        byte_offset=byte_offset,
    )


def _line_is_negated(text: str, offset: int) -> bool:
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end].lower()
    return "no " in line or "not " in line or "without " in line


def _portable_path(path: Path) -> str:
    parts = path.parts
    if "article_exhibits" in parts:
        idx = parts.index("article_exhibits")
        return "/".join(parts[idx:])
    return path.name
