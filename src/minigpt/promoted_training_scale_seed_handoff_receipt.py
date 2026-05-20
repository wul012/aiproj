from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict
from minigpt.report_utils import string_list


RECEIPT_TYPE = "promoted_training_scale_seed_handoff_automation"


def load_promoted_training_scale_seed_handoff_automation_receipt(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted seed handoff automation receipt must be a JSON object")
    return dict(payload)


def check_promoted_training_scale_seed_handoff_automation_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    payload = as_dict(receipt)
    receipt_type = str(payload.get("receipt_type") or "")
    decision = str(payload.get("automation_decision") or "")
    blocking_source = payload.get("automation_blocking_source")
    failed_requirements = string_list(payload.get("failed_requirements"))
    schema_version = _int(payload.get("schema_version"))
    exit_code = _int(payload.get("automation_exit_code"))
    issues: list[str] = []
    if receipt_type != RECEIPT_TYPE:
        issues.append(f"receipt_type must be {RECEIPT_TYPE}")
    if schema_version < 1:
        issues.append("schema_version must be >= 1")
    if decision not in {"continue", "stop"}:
        issues.append("automation_decision must be continue or stop")
    if decision == "stop" and exit_code == 0:
        issues.append("stop decision must carry a non-zero automation_exit_code")
    if decision == "continue" and exit_code != 0:
        issues.append("continue decision must carry automation_exit_code=0")
    if decision == "stop" and not blocking_source:
        issues.append("stop decision must carry automation_blocking_source")
    if decision == "continue" and blocking_source:
        issues.append("continue decision must not carry automation_blocking_source")
    if blocking_source == "automation_gate" and not failed_requirements:
        issues.append("automation_gate blocking source must include failed_requirements")
    status = "pass" if not issues else "fail"
    checker_exit_code = 0 if status == "pass" and decision == "continue" else 1
    return {
        "schema_version": schema_version,
        "receipt_type": receipt_type,
        "status": status,
        "decision": decision,
        "exit_code": exit_code,
        "checker_exit_code": checker_exit_code,
        "blocking_source": str(blocking_source) if blocking_source is not None else None,
        "failed_requirements": failed_requirements,
        "issue_count": len(issues),
        "issues": issues,
    }


def render_promoted_training_scale_seed_handoff_automation_receipt_check(check: dict[str, Any]) -> str:
    rows = [
        ("receipt_check_status", check.get("status")),
        ("receipt_decision", check.get("decision")),
        ("receipt_exit_code", check.get("exit_code")),
        ("receipt_checker_exit_code", check.get("checker_exit_code")),
        ("receipt_blocking_source", check.get("blocking_source")),
        ("receipt_failed_requirements", json.dumps(check.get("failed_requirements"), ensure_ascii=False)),
        ("receipt_issue_count", check.get("issue_count")),
        ("receipt_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


__all__ = [
    "RECEIPT_TYPE",
    "check_promoted_training_scale_seed_handoff_automation_receipt",
    "load_promoted_training_scale_seed_handoff_automation_receipt",
    "render_promoted_training_scale_seed_handoff_automation_receipt_check",
]
