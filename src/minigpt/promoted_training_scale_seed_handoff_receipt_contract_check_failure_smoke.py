from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import CONTRACT_SUMMARY_JSON_FILENAME
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check import (
    check_promoted_training_scale_seed_handoff_receipt_contract_summary,
    resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs,
)
from minigpt.report_utils import html_escape


FAILURE_SMOKE_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.json"
FAILURE_SMOKE_CSV_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.csv"
FAILURE_SMOKE_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.txt"
FAILURE_SMOKE_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.md"
FAILURE_SMOKE_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.html"

SCENARIOS = [
    {
        "name": "baseline",
        "tamper": "none",
        "expected_status": "pass",
        "expected_failed_families": [],
        "expected_failed_targets": [],
    },
    {
        "name": "tamper_summary_field",
        "tamper": "receipt_schema_version",
        "expected_status": "fail",
        "expected_failed_families": ["summary_field"],
        "expected_failed_targets": ["summary.receipt_schema_version"],
    },
    {
        "name": "tamper_contract_profile",
        "tamper": "contract_check_type_summary",
        "expected_status": "fail",
        "expected_failed_families": ["contract_profile", "summary_field"],
        "expected_failed_targets": ["summary.contract_check_type_summary"],
    },
    {
        "name": "tamper_sidecar",
        "tamper": "html_sidecar",
        "expected_status": "fail",
        "expected_failed_families": ["sidecar"],
        "expected_failed_targets": ["promoted_training_scale_seed_handoff_receipt_contract_summary.html"],
    },
]


def run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke(
    summary_path: str | Path,
    out_dir: str | Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    resolved_summary_path = resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(summary_path)
    source_dir = resolved_summary_path.parent
    root = Path(out_dir)
    if root.exists() and any(root.iterdir()):
        if not force:
            raise FileExistsError(f"output directory is not empty; pass force=True to replace it: {root}")
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    scenario_root = root / "scenarios"
    rows = [run_scenario(source_dir, scenario_root, scenario) for scenario in SCENARIOS]
    issues = scenario_issues(rows)
    return {
        "failure_smoke_version": 1,
        "status": "pass" if not issues else "fail",
        "decision": "failure_matrix_verified" if not issues else "review_failure_matrix",
        "source_summary_path": str(resolved_summary_path),
        "source_summary_dir": str(source_dir),
        "scenario_count": len(rows),
        "passed_scenario_count": sum(1 for row in rows if row.get("status") == "pass"),
        "failed_scenario_count": sum(1 for row in rows if row.get("status") != "pass"),
        "verified_scenario_count": sum(1 for row in rows if row.get("verification_status") == "pass"),
        "failed_verification_count": sum(1 for row in rows if row.get("verification_status") != "pass"),
        "scenario_rows": rows,
        "issue_count": len(issues),
        "issues": issues,
    }


def run_scenario(source_dir: Path, scenario_root: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_dir = scenario_root / str(scenario["name"])
    summary_dir = scenario_dir / "summary"
    check_dir = scenario_dir / "check"
    shutil.copytree(source_dir, summary_dir)
    apply_tamper(summary_dir, str(scenario["tamper"]))
    check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)
    check_outputs = write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(check, check_dir)
    failed_families = failed_family_names(check)
    expected_failed_families = sorted(str(item) for item in scenario["expected_failed_families"])
    expected_failed_targets = [str(item) for item in scenario["expected_failed_targets"]]
    failed_targets = sorted({str(row.get("target")) for row in check.get("failed_check_targets", []) if row.get("target")})
    status_matches = check.get("status") == scenario["expected_status"]
    family_matches = failed_families == expected_failed_families
    target_matches = expected_targets_present(expected_failed_targets, failed_targets)
    verification_status = "pass" if status_matches and family_matches and target_matches else "fail"
    return {
        "scenario": scenario["name"],
        "tamper": scenario["tamper"],
        "status": check.get("status"),
        "expected_status": scenario["expected_status"],
        "status_matches": status_matches,
        "verification_status": verification_status,
        "failed_families": failed_families,
        "expected_failed_families": expected_failed_families,
        "family_matches": family_matches,
        "failed_targets": failed_targets,
        "expected_failed_targets": expected_failed_targets,
        "target_matches": target_matches,
        "failed_check_target_count": check.get("failed_check_target_count"),
        "summary_field_failed_count": family_failed_count(check, "summary_field"),
        "contract_profile_failed_count": family_failed_count(check, "contract_profile"),
        "sidecar_failed_count": family_failed_count(check, "sidecar"),
        "summary_dir": str(summary_dir),
        "check_json": check_outputs["json"],
        "check_markdown": check_outputs["markdown"],
        "check_html": check_outputs["html"],
    }


def apply_tamper(summary_dir: Path, tamper: str) -> None:
    if tamper == "none":
        return
    summary_path = summary_dir / CONTRACT_SUMMARY_JSON_FILENAME
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if tamper == "receipt_schema_version":
        payload["receipt_schema_version"] = 2
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    if tamper == "contract_check_type_summary":
        type_summary = payload.get("contract_check_type_summary")
        if not isinstance(type_summary, list) or not type_summary:
            raise ValueError("contract_check_type_summary must contain at least one row")
        first = dict(type_summary[0])
        first["failed_count"] = int(first.get("failed_count") or 0) + 7
        type_summary[0] = first
        payload["contract_check_type_summary"] = type_summary
        summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    if tamper == "html_sidecar":
        html_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.html"
        html_path.write_text(html_path.read_text(encoding="utf-8") + "\n<!-- v457 stale sidecar -->\n", encoding="utf-8")
        return
    raise ValueError(f"unknown tamper scenario: {tamper}")


def failed_family_names(check: dict[str, Any]) -> list[str]:
    rows = check.get("check_family_summary")
    if not isinstance(rows, list):
        return []
    return sorted(str(row.get("family")) for row in rows if isinstance(row, dict) and row.get("failed_count"))


def family_failed_count(check: dict[str, Any], family: str) -> int:
    rows = check.get("check_family_summary")
    if not isinstance(rows, list):
        return 0
    for row in rows:
        if isinstance(row, dict) and row.get("family") == family:
            return int(row.get("failed_count") or 0)
    return 0


def expected_targets_present(expected: list[str], actual: list[str]) -> bool:
    return all(any(target.endswith(item) or item in target for target in actual) for item in expected)


def scenario_issues(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        if not row.get("status_matches"):
            issues.append(
                f"{row.get('scenario')} status expected {row.get('expected_status')} but got {row.get('status')}"
            )
        if not row.get("family_matches"):
            issues.append(
                f"{row.get('scenario')} failed families expected {row.get('expected_failed_families')} "
                f"but got {row.get('failed_families')}"
            )
        if not row.get("target_matches"):
            issues.append(
                f"{row.get('scenario')} failed targets missing {row.get('expected_failed_targets')} "
                f"from {row.get('failed_targets')}"
            )
    return issues


def render_failure_smoke_text(summary: dict[str, Any]) -> str:
    rows = [
        ("receipt_contract_summary_check_failure_smoke_status", summary.get("status")),
        ("receipt_contract_summary_check_failure_smoke_decision", summary.get("decision")),
        ("receipt_contract_summary_check_failure_smoke_scenario_count", summary.get("scenario_count")),
        ("receipt_contract_summary_check_failure_smoke_verified_scenario_count", summary.get("verified_scenario_count")),
        ("receipt_contract_summary_check_failure_smoke_failed_verification_count", summary.get("failed_verification_count")),
        ("receipt_contract_summary_check_failure_smoke_issue_count", summary.get("issue_count")),
        ("receipt_contract_summary_check_failure_smoke_issues", json.dumps(summary.get("issues"), ensure_ascii=False)),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_failure_smoke_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Promoted Receipt Contract Summary-Check Failure Smoke",
        "",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- Scenario count: `{summary.get('scenario_count')}`",
        f"- Failed verification count: `{summary.get('failed_verification_count')}`",
        "",
        "## Scenarios",
        "",
        "| Scenario | Tamper | Check status | Verification | Failed families | Failed targets |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in scenario_rows(summary):
        lines.append(
            f"| {row.get('scenario')} | {row.get('tamper')} | {row.get('status')} | "
            f"{row.get('verification_status')} | {json.dumps(row.get('failed_families'), ensure_ascii=False)} | "
            f"{json.dumps(row.get('failed_targets'), ensure_ascii=False)} |"
        )
    lines.extend(["", "## Issues", ""])
    issues = summary.get("issues")
    if isinstance(issues, list) and issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_failure_smoke_html(summary: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('scenario'))}</td>"
        f"<td>{html_escape(row.get('tamper'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('verification_status'))}</td>"
        f"<td>{html_escape(json.dumps(row.get('failed_families'), ensure_ascii=False))}</td>"
        f"<td>{html_escape(json.dumps(row.get('failed_targets'), ensure_ascii=False))}</td>"
        "</tr>"
        for row in scenario_rows(summary)
    )
    issues = summary.get("issues")
    issue_items = ""
    if isinstance(issues, list) and issues:
        issue_items = "\n".join(f"<li>{html_escape(issue)}</li>" for issue in issues)
    else:
        issue_items = "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT receipt contract summary-check failure smoke</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f5f7f8; color: #172029; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dee3; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dee3; border-radius: 8px; padding: 10px; background: #fbfcfd; }}
.metric span {{ display: block; color: #5a6871; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #d7dee3; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #eef3f6; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT receipt contract summary-check failure smoke</h1>
<section>
<h2>Summary</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(summary.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(summary.get('decision'))}</strong></div>
<div class="metric"><span>Scenarios</span><strong>{html_escape(summary.get('scenario_count'))}</strong></div>
<div class="metric"><span>Failed verifications</span><strong>{html_escape(summary.get('failed_verification_count'))}</strong></div>
</div>
</section>
<section>
<h2>Scenarios</h2>
<table>
<thead>
<tr><th>Scenario</th><th>Tamper</th><th>Check status</th><th>Verification</th><th>Failed families</th><th>Failed targets</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</section>
<section>
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
</main>
</body>
</html>
"""


def scenario_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = summary.get("scenario_rows")
    if not isinstance(value, list):
        return []
    return [dict(row) for row in value if isinstance(row, dict)]


def write_failure_smoke_outputs(summary: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / FAILURE_SMOKE_JSON_FILENAME,
        "csv": root / FAILURE_SMOKE_CSV_FILENAME,
        "text": root / FAILURE_SMOKE_TEXT_FILENAME,
        "markdown": root / FAILURE_SMOKE_MARKDOWN_FILENAME,
        "html": root / FAILURE_SMOKE_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with paths["csv"].open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scenario",
                "tamper",
                "status",
                "expected_status",
                "verification_status",
                "failed_families",
                "expected_failed_families",
                "failed_targets",
                "expected_failed_targets",
                "failed_check_target_count",
            ],
        )
        writer.writeheader()
        for row in scenario_rows(summary):
            writer.writerow({key: json.dumps(row.get(key), ensure_ascii=False) if isinstance(row.get(key), list) else row.get(key) for key in writer.fieldnames})
    paths["text"].write_text(render_failure_smoke_text(summary), encoding="utf-8")
    paths["markdown"].write_text(render_failure_smoke_markdown(summary), encoding="utf-8")
    paths["html"].write_text(render_failure_smoke_html(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "FAILURE_SMOKE_CSV_FILENAME",
    "FAILURE_SMOKE_HTML_FILENAME",
    "FAILURE_SMOKE_JSON_FILENAME",
    "FAILURE_SMOKE_MARKDOWN_FILENAME",
    "FAILURE_SMOKE_TEXT_FILENAME",
    "render_failure_smoke_html",
    "render_failure_smoke_markdown",
    "render_failure_smoke_text",
    "run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke",
    "write_failure_smoke_outputs",
]
