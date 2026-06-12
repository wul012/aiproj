from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

SCAN_DIRS = ("scripts", "src/minigpt", "tests")
REPEATED_TOKEN = "receipt_index"
LEGACY_REPEAT_WARN = 1
LONG_NAME_WARN = 96

SHORT_ALIAS_POLICY = {
    "publication receipt index": "pub_receipt_index",
    "publication receipt review": "pub_receipt_review",
    "receipt contract check": "receipt_contract_check",
    "randomized holdout publication": "holdout_pub",
}


def build_publication_naming_readability_report(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    rows = sorted(_scan_paths(project_root), key=lambda row: (-int(row["repeat_count"]), -int(row["name_length"]), str(row["path"])))
    repeated_rows = [row for row in rows if int(row["repeat_count"]) > LEGACY_REPEAT_WARN]
    long_rows = [row for row in rows if int(row["name_length"]) > LONG_NAME_WARN]
    status = "watch" if repeated_rows or long_rows else "pass"
    return {
        "schema_version": 1,
        "title": "MiniGPT publication naming readability stopgap v1130",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "publication_short_alias_policy_ready",
        "summary": {
            "status": status,
            "decision": "publication_short_alias_policy_ready",
            "scanned_file_count": len(rows),
            "repeated_receipt_index_file_count": len(repeated_rows),
            "long_name_file_count": len(long_rows),
            "max_name_length": max([int(row["name_length"]) for row in rows], default=0),
            "new_file_repeat_limit": LEGACY_REPEAT_WARN,
            "new_file_name_length_limit": LONG_NAME_WARN,
            "short_alias_count": len(SHORT_ALIAS_POLICY),
            "policy_ready": True,
        },
        "policy": {
            "scope": list(SCAN_DIRS),
            "legacy_files_are_watch_items": True,
            "new_publication_files_must_use_short_alias": True,
            "repeated_token": REPEATED_TOKEN,
            "repeat_limit": LEGACY_REPEAT_WARN,
            "name_length_limit": LONG_NAME_WARN,
            "aliases": dict(SHORT_ALIAS_POLICY),
        },
        "rows": rows[:80],
        "recommendations": [
            "Keep legacy receipt_index chains stable unless a dedicated compatibility migration exists.",
            "Put new publication scripts under scripts/publication/ with short names.",
            "Prefer pub_receipt_index, pub_receipt_review, receipt_contract_check, and holdout_pub aliases for new files.",
            "Treat this report as a stopgap policy, not a mass rename request.",
        ],
        "csv_fieldnames": ["path", "kind", "name_length", "repeat_count", "status", "recommendation"],
    }


def write_publication_naming_readability_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem="publication_naming_readability_v1130",
        row_title="Naming Pressure Rows",
    )


def resolve_exit_code(report: dict[str, Any], *, require_policy_ready: bool = False, require_clean_new_names: bool = False) -> int:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    if require_policy_ready and summary.get("policy_ready") is not True:
        return 1
    if require_clean_new_names and report.get("status") != "pass":
        return 1
    return 0


def _scan_paths(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in SCAN_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            name = path.name
            repeat_count = name.count(REPEATED_TOKEN)
            name_length = len(name)
            if repeat_count <= LEGACY_REPEAT_WARN and name_length <= LONG_NAME_WARN:
                continue
            rel = path.relative_to(root).as_posix()
            rows.append(
                {
                    "path": rel,
                    "kind": directory,
                    "name_length": name_length,
                    "repeat_count": repeat_count,
                    "status": "legacy-watch",
                    "recommendation": _recommendation(name_length, repeat_count),
                }
            )
    return rows


def _recommendation(name_length: int, repeat_count: int) -> str:
    if repeat_count > LEGACY_REPEAT_WARN:
        return "Use a short publication alias for the next file in this family."
    if name_length > LONG_NAME_WARN:
        return "Shorten future names or move the repeated context into the package path."
    return "No action."


__all__ = [
    "LONG_NAME_WARN",
    "REPEATED_TOKEN",
    "SCAN_DIRS",
    "SHORT_ALIAS_POLICY",
    "build_publication_naming_readability_report",
    "resolve_exit_code",
    "write_publication_naming_readability_outputs",
]
