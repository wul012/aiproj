from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.generation_profiles import DEFAULT_GENERATION_PROFILE_ID, NEWLINE_SUPPRESSION_PROFILE_ID
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


GENERATION_PROFILE_CONTRACT_CHECK_JSON_FILENAME = "generation_profile_contract_check.json"
GENERATION_PROFILE_CONTRACT_CHECK_CSV_FILENAME = "generation_profile_contract_check.csv"
GENERATION_PROFILE_CONTRACT_CHECK_TEXT_FILENAME = "generation_profile_contract_check.txt"
GENERATION_PROFILE_CONTRACT_CHECK_MARKDOWN_FILENAME = "generation_profile_contract_check.md"
GENERATION_PROFILE_CONTRACT_CHECK_HTML_FILENAME = "generation_profile_contract_check.html"

GENERATION_PROFILES_ENDPOINT_JSON_FILENAME = "generation-profiles.json"
EXPECTED_GENERATION_PROFILE_IDS = (DEFAULT_GENERATION_PROFILE_ID, NEWLINE_SUPPRESSION_PROFILE_ID)
EXPECTED_SUPPRESSED_TOKEN_TEXTS = ("\n", "\r")


def resolve_generation_profiles_source(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / GENERATION_PROFILES_ENDPOINT_JSON_FILENAME
    return candidate


def build_generation_profile_contract_check(
    profiles_path: str | Path,
    *,
    health_path: str | Path,
    api_response_path: str | Path,
    playground_html_path: str | Path,
    default_output_path: str | Path,
    profile_output_path: str | Path,
    title: str = "MiniGPT generation profile contract check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    profiles_source = resolve_generation_profiles_source(profiles_path)
    health_source = Path(health_path)
    api_source = Path(api_response_path)
    playground_source = Path(playground_html_path)
    default_output_source = Path(default_output_path)
    profile_output_source = Path(profile_output_path)

    profiles, profile_source_row = _read_json_source("profiles", profiles_source)
    health, health_source_row = _read_json_source("health", health_source)
    api_response, api_source_row = _read_json_source("api_response", api_source)
    playground_html, playground_source_row = _read_text_source("playground_html", playground_source)
    default_output, default_source_row = _read_text_source("default_output", default_output_source)
    profile_output, profile_source_output_row = _read_text_source("profile_output", profile_output_source)

    endpoint_ids = _profile_ids(profiles)
    health_ids = _profile_ids({"profiles": health.get("generation_profiles")})
    suppression_profile = _profile_by_id(profiles, NEWLINE_SUPPRESSION_PROFILE_ID)
    suppression_blocked_texts = _string_tuple(suppression_profile.get("blocked_token_texts"))
    api_blocked_texts = _string_tuple(api_response.get("blocked_token_texts"))

    checks = [
        _source_check(profile_source_row),
        _source_check(health_source_row),
        _source_check(api_source_row),
        _source_check(playground_source_row),
        _source_check(default_source_row),
        _source_check(profile_source_output_row),
        _check(
            "profiles_status_ok",
            "endpoint",
            "profiles.status",
            "ok",
            profiles.get("status"),
            profiles.get("status") == "ok",
            "generation profile endpoint status must be ok",
        ),
        _check(
            "profiles_default_id",
            "endpoint",
            "profiles.default_generation_profile_id",
            DEFAULT_GENERATION_PROFILE_ID,
            profiles.get("default_generation_profile_id"),
            profiles.get("default_generation_profile_id") == DEFAULT_GENERATION_PROFILE_ID,
            "endpoint default profile must stay stable",
        ),
        _check(
            "profiles_expected_ids",
            "endpoint",
            "profiles[].id",
            list(EXPECTED_GENERATION_PROFILE_IDS),
            endpoint_ids,
            all(profile_id in endpoint_ids for profile_id in EXPECTED_GENERATION_PROFILE_IDS),
            "endpoint must publish default and newline-suppression profiles",
        ),
        _check(
            "profiles_count_matches",
            "endpoint",
            "profiles.profile_count",
            len(endpoint_ids),
            profiles.get("profile_count"),
            profiles.get("profile_count") == len(endpoint_ids),
            "profile_count must match the profile list length",
        ),
        _token_check("suppression_profile_blocks_newline", "endpoint", suppression_blocked_texts, "\n"),
        _token_check("suppression_profile_blocks_carriage_return", "endpoint", suppression_blocked_texts, "\r"),
        _check(
            "health_profiles_endpoint",
            "health",
            "health.generation_profiles_endpoint",
            "/api/generation-profiles",
            health.get("generation_profiles_endpoint"),
            health.get("generation_profiles_endpoint") == "/api/generation-profiles",
            "health payload must advertise the runtime profile endpoint",
        ),
        _check(
            "health_profile_ids_match_endpoint",
            "health",
            "health.generation_profiles[].id",
            endpoint_ids,
            health_ids,
            health_ids == endpoint_ids,
            "health profile ids must match endpoint profile ids",
        ),
        _check(
            "api_generation_profile",
            "api",
            "api.generation_profile",
            NEWLINE_SUPPRESSION_PROFILE_ID,
            api_response.get("generation_profile"),
            api_response.get("generation_profile") == NEWLINE_SUPPRESSION_PROFILE_ID,
            "API response must echo the selected suppression profile",
        ),
        _token_check("api_blocks_newline", "api", api_blocked_texts, "\n"),
        _token_check("api_blocks_carriage_return", "api", api_blocked_texts, "\r"),
        _check(
            "api_blocked_token_count_positive",
            "api",
            "api.blocked_token_count",
            ">0",
            api_response.get("blocked_token_count"),
            _int(api_response.get("blocked_token_count")) > 0,
            "API response must show that at least one token was masked",
        ),
        _check(
            "api_generated_contains_loss",
            "api",
            "api.generated",
            "contains loss",
            api_response.get("generated"),
            "loss" in str(api_response.get("generated", "")).lower(),
            "suppression-profile API sample must preserve the target loss surface",
        ),
        _check(
            "api_continuation_has_no_newline",
            "api",
            "api.continuation",
            "no newline",
            api_response.get("continuation"),
            "\n" not in str(api_response.get("continuation", "")) and "\r" not in str(api_response.get("continuation", "")),
            "suppression-profile API continuation should not contain newline separators",
        ),
        _html_check("playground_has_profile_select", playground_html, "generationProfileSelect"),
        _html_check("playground_fetches_profile_endpoint", playground_html, "/api/generation-profiles"),
        _html_check("playground_has_profile_loader", playground_html, "loadGenerationProfiles"),
        _html_check("playground_has_cli_profile_flag", playground_html, "--generation-profile"),
        _check(
            "cli_outputs_differ",
            "cli",
            "default_output vs profile_output",
            "different",
            {"default": default_output, "profile": profile_output},
            default_output != profile_output,
            "default and suppression-profile samples should be distinguishable",
        ),
        _check(
            "cli_default_has_newline_split",
            "cli",
            "default_output",
            "contains newline",
            default_output,
            "\n" in default_output or "\r" in default_output,
            "archived default sample demonstrates the pre-profile newline split",
        ),
        _check(
            "cli_profile_has_no_newline",
            "cli",
            "profile_output",
            "no newline",
            profile_output.strip(),
            "\n" not in profile_output.strip() and "\r" not in profile_output.strip(),
            "archived suppression-profile sample should remove newline separators",
        ),
        _check(
            "cli_profile_contains_loss",
            "cli",
            "profile_output",
            "contains loss",
            profile_output.strip(),
            "loss" in profile_output.lower(),
            "archived suppression-profile sample should keep the loss term readable",
        ),
    ]
    failed_checks = [check for check in checks if check.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "generation_profile_contract_ready" if status == "pass" else "fix_generation_profile_contract",
        "failed_count": len(failed_checks),
        "issues": [_issue_from_check(check) for check in failed_checks],
        "checks": checks,
        "sources": {
            row["id"]: row for row in [
                profile_source_row,
                health_source_row,
                api_source_row,
                playground_source_row,
                default_source_row,
                profile_source_output_row,
            ]
        },
        "summary": {
            "endpoint_profile_ids": endpoint_ids,
            "health_profile_ids": health_ids,
            "expected_profile_ids": list(EXPECTED_GENERATION_PROFILE_IDS),
            "api_generation_profile": api_response.get("generation_profile"),
            "api_blocked_token_count": api_response.get("blocked_token_count"),
            "default_output_has_newline": "\n" in default_output or "\r" in default_output,
            "profile_output_has_newline": "\n" in profile_output.strip() or "\r" in profile_output.strip(),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _read_json_source(source_id: str, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source = _source_row(source_id, path)
    if not path.is_file():
        source["read_status"] = "missing"
        return {}, source
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        source["read_status"] = "error"
        source["error"] = str(exc)
        return {}, source
    if not isinstance(payload, dict):
        source["read_status"] = "not_object"
        source["error"] = "source JSON must be an object"
        return {}, source
    source["read_status"] = "ok"
    return dict(payload), source


def _read_text_source(source_id: str, path: Path) -> tuple[str, dict[str, Any]]:
    source = _source_row(source_id, path)
    if not path.is_file():
        source["read_status"] = "missing"
        return "", source
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        source["read_status"] = "error"
        source["error"] = str(exc)
        return "", source
    source["read_status"] = "ok"
    return text, source


def _source_row(source_id: str, path: Path) -> dict[str, Any]:
    return {
        "id": source_id,
        "path": str(path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "read_status": "pending",
    }


def _source_check(source: dict[str, Any]) -> dict[str, Any]:
    return _check(
        f"{source.get('id')}_readable",
        "source",
        str(source.get("path")),
        "ok",
        source.get("read_status"),
        source.get("read_status") == "ok",
        f"{source.get('id')} source must be readable",
    )


def _profile_ids(payload: dict[str, Any]) -> list[str]:
    return [str(profile.get("id")) for profile in list_of_dicts(payload.get("profiles")) if profile.get("id")]


def _profile_by_id(payload: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for profile in list_of_dicts(payload.get("profiles")):
        if profile.get("id") == profile_id:
            return profile
    return {}


def _token_check(check_id: str, category: str, token_texts: tuple[str, ...], token: str) -> dict[str, Any]:
    label = "\\n" if token == "\n" else "\\r" if token == "\r" else token
    return _check(
        check_id,
        category,
        "blocked_token_texts",
        f"contains {label}",
        list(token_texts),
        token in token_texts,
        f"blocked token texts must include {label}",
    )


def _html_check(check_id: str, html: str, marker: str) -> dict[str, Any]:
    return _check(
        check_id,
        "playground",
        "playground_html",
        f"contains {marker}",
        marker if marker in html else "missing",
        marker in html,
        f"playground HTML must include {marker}",
    )


def _check(
    check_id: str,
    category: str,
    target: str,
    expected: Any,
    actual: Any,
    passed: bool,
    detail: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "category": category,
        "target": target,
        "expected": expected,
        "actual": actual,
        "status": "pass" if passed else "fail",
        "detail": detail,
    }


def _issue_from_check(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": check.get("id"),
        "category": check.get("category"),
        "target": check.get("target"),
        "expected": check.get("expected"),
        "actual": check.get("actual"),
        "detail": check.get("detail"),
    }


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value is None or isinstance(value, dict):
        return ()
    return (str(value),)


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("checks"))


def issues(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("issues"))


def summary(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(report.get("summary"))


__all__ = [
    "EXPECTED_GENERATION_PROFILE_IDS",
    "EXPECTED_SUPPRESSED_TOKEN_TEXTS",
    "GENERATION_PROFILE_CONTRACT_CHECK_CSV_FILENAME",
    "GENERATION_PROFILE_CONTRACT_CHECK_HTML_FILENAME",
    "GENERATION_PROFILE_CONTRACT_CHECK_JSON_FILENAME",
    "GENERATION_PROFILE_CONTRACT_CHECK_MARKDOWN_FILENAME",
    "GENERATION_PROFILE_CONTRACT_CHECK_TEXT_FILENAME",
    "GENERATION_PROFILES_ENDPOINT_JSON_FILENAME",
    "build_generation_profile_contract_check",
    "checks",
    "issues",
    "resolve_exit_code",
    "resolve_generation_profiles_source",
    "summary",
]
