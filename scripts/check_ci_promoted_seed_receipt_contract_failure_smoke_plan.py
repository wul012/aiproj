from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from minigpt.report_utils import as_dict, html_escape as _e, markdown_cell as _md, write_json_payload  # noqa: E402
from scripts.run_ci_promoted_seed_receipt_contract_failure_smoke import PLAN_JSON_FILENAME  # noqa: E402

CHECK_JSON_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan_check.json"
CHECK_TEXT_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan_check.txt"
CHECK_MARKDOWN_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan_check.md"
CHECK_HTML_FILENAME = "ci_promoted_seed_receipt_contract_failure_smoke_plan_check.html"

EXPECTED_WRAPPER = "run_ci_promoted_seed_receipt_contract_failure_smoke"
EXPECTED_DECISION = "receipt_contract_failure_smoke_verified"
EXPECTED_COMMANDS = {
    "receipt_contract_summary": 0,
    "receipt_contract_failure_smoke": 0,
}
EXPECTED_FAILURE_SMOKE_SUMMARY = {
    "available": True,
    "parse_status": "pass",
    "status": "pass",
    "scenario_count": 4,
    "verified_scenario_count": 4,
    "failed_verification_count": 0,
}
REQUIRED_ARTIFACTS = (
    "contract_summary_json",
    "failure_smoke_json",
    "failure_smoke_csv",
    "failure_smoke_html",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the CI promoted seed receipt failure-smoke wrapper plan.")
    parser.add_argument(
        "plan",
        type=Path,
        nargs="?",
        default=ROOT / "runs" / "promoted-seed-receipt-contract-failure-smoke-ci",
        help="Path to the wrapper plan JSON file or its output directory.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "ci-promoted-seed-receipt-contract-failure-smoke-plan-check",
    )
    parser.add_argument("--require-pass", action="store_true", help="Explicitly require a passing plan check.")
    parser.add_argument("--no-fail", action="store_true", help="Write outputs but do not exit non-zero on failure.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    plan_path = resolve_plan_path(args.plan)
    plan = load_plan(plan_path)
    report = check_plan(plan, plan_path=plan_path)
    outputs = write_check_outputs(report, args.out_dir)
    print(render_check_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    require_pass = args.require_pass or not args.no_fail
    if report["status"] == "fail" and require_pass:
        raise SystemExit(1)


def resolve_plan_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / PLAN_JSON_FILENAME
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"CI promoted seed receipt failure-smoke plan not found: {path}")


def load_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"plan JSON must contain an object: {path}")
    return dict(payload)


def check_plan(plan: dict[str, Any], *, plan_path: Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    _append_check(checks, "plan:wrapper", "wrapper", EXPECTED_WRAPPER, plan.get("wrapper"), "Wrapper identity must remain stable.")
    _append_check(checks, "plan:status", "status", "pass", plan.get("status"), "Wrapper plan must record a successful run.")
    _append_check(checks, "plan:decision", "decision", EXPECTED_DECISION, plan.get("decision"), "Wrapper decision must preserve the verified smoke outcome.")

    commands = _commands_by_name(plan)
    for name, expected_returncode in EXPECTED_COMMANDS.items():
        command = commands.get(name, {})
        _append_check(
            checks,
            f"command:{name}:present",
            f"commands.{name}",
            True,
            bool(command),
            "Required child command must be recorded in the wrapper plan.",
        )
        _append_check(
            checks,
            f"command:{name}:returncode",
            f"commands.{name}.returncode",
            expected_returncode,
            command.get("returncode"),
            "Required child command must complete successfully.",
        )

    smoke = as_dict(plan.get("failure_smoke_summary"))
    for key, expected in EXPECTED_FAILURE_SMOKE_SUMMARY.items():
        _append_check(
            checks,
            f"failure_smoke_summary:{key}",
            f"failure_smoke_summary.{key}",
            expected,
            smoke.get(key),
            "Failure-smoke summary must keep the expected verified matrix result.",
        )

    artifacts = as_dict(as_dict(plan.get("artifact_digest")).get("artifacts"))
    artifact_rows = _artifact_rows(artifacts, checks)
    failed_checks = [item for item in checks if item.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "continue" if status == "pass" else "fix-receipt-failure-smoke-plan",
        "source_plan": "" if plan_path is None else str(plan_path),
        "source_handoff": plan.get("source_handoff"),
        "wrapper": plan.get("wrapper"),
        "check_count": len(checks),
        "failed_count": len(failed_checks),
        "artifact_count": len(artifact_rows),
        "artifact_failure_count": sum(1 for row in artifact_rows if row.get("status") != "pass"),
        "failure_smoke_summary": smoke,
        "artifacts": artifact_rows,
        "checks": checks,
        "issues": [_issue_from_check(item) for item in failed_checks],
    }


def render_check_text(report: dict[str, Any]) -> str:
    smoke = as_dict(report.get("failure_smoke_summary"))
    rows: list[tuple[str, Any]] = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("source_plan", report.get("source_plan")),
        ("source_handoff", report.get("source_handoff")),
        ("wrapper", report.get("wrapper")),
        ("failure_smoke_available", smoke.get("available")),
        ("failure_smoke_status", smoke.get("status")),
        ("failure_smoke_scenario_count", smoke.get("scenario_count")),
        ("failure_smoke_failed_verification_count", smoke.get("failed_verification_count")),
    ]
    for artifact in _list_of_dicts(report.get("artifacts")):
        rows.append((f"{artifact.get('name')}_status", artifact.get("status")))
        rows.append((f"{artifact.get('name')}_actual_sha256", artifact.get("actual_sha256")))
    for index, issue in enumerate(_list_of_dicts(report.get("issues")), start=1):
        rows.append((f"issue_{index}_code", issue.get("code")))
        rows.append((f"issue_{index}_target", issue.get("target")))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_check_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CI promoted seed receipt failure-smoke plan check",
        "",
        f"- Status: `{_md(report.get('status'))}`",
        f"- Decision: `{_md(report.get('decision'))}`",
        f"- Source plan: `{_md(report.get('source_plan'))}`",
        f"- Source handoff: `{_md(report.get('source_handoff'))}`",
        "",
        "## Checks",
        "",
        "| ID | Target | Expected | Actual | Status | Detail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in _list_of_dicts(report.get("checks")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("id")),
                    _md(item.get("target")),
                    _md(item.get("expected")),
                    _md(item.get("actual")),
                    _md(item.get("status")),
                    _md(item.get("detail")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Artifacts", "", "| Name | Status | Size | SHA-256 | Path |", "| --- | --- | ---: | --- | --- |"])
    for item in _list_of_dicts(report.get("artifacts")):
        lines.append(
            f"| {_md(item.get('name'))} | {_md(item.get('status'))} | {_md(item.get('actual_size_bytes'))} | "
            f"{_md(item.get('actual_sha256'))} | {_md(item.get('path'))} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_check_html(report: dict[str, Any]) -> str:
    checks = "".join(_check_row(item) for item in _list_of_dicts(report.get("checks")))
    artifacts = "".join(_artifact_row(item) for item in _list_of_dicts(report.get("artifacts")))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Failed", report.get("failed_count")),
        ("Artifacts", report.get("artifact_count")),
        ("Artifact failures", report.get("artifact_failure_count")),
        ("Wrapper", report.get("wrapper")),
        ("Source handoff", report.get("source_handoff")),
        ("Source plan", report.get("source_plan")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            "<title>CI promoted seed receipt failure-smoke plan check</title>",
            _style(),
            "</head>",
            "<body>",
            "<header><h1>CI promoted seed receipt failure-smoke plan check</h1><p>Revalidates the v459 wrapper plan, child command return codes, failure-smoke summary, and artifact digests.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Checks</h2><table><tr><th>ID</th><th>Target</th><th>Expected</th><th>Actual</th><th>Status</th><th>Detail</th></tr>"
            + checks
            + "</table></section>",
            "<section><h2>Artifacts</h2><table><tr><th>Name</th><th>Status</th><th>Size</th><th>SHA-256</th><th>Path</th></tr>"
            + artifacts
            + "</table></section>",
            "<footer>Generated by MiniGPT CI promoted receipt failure-smoke plan check.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_check_outputs(report: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / CHECK_JSON_FILENAME,
        "text": out_dir / CHECK_TEXT_FILENAME,
        "markdown": out_dir / CHECK_MARKDOWN_FILENAME,
        "html": out_dir / CHECK_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    paths["text"].write_text(render_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_check_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _artifact_rows(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in REQUIRED_ARTIFACTS:
        expected = as_dict(artifacts.get(name))
        path_text = str(expected.get("path") or "")
        actual = _actual_digest(Path(path_text)) if path_text else _missing_actual()
        row = {
            "name": name,
            "path": path_text,
            "expected_exists": bool(expected.get("exists")),
            "actual_exists": bool(actual.get("exists")),
            "expected_size_bytes": _int_or_zero(expected.get("size_bytes")),
            "actual_size_bytes": _int_or_zero(actual.get("size_bytes")),
            "expected_sha256": str(expected.get("sha256") or ""),
            "actual_sha256": str(actual.get("sha256") or ""),
        }
        row["status"] = "pass" if _artifact_matches(row) else "fail"
        rows.append(row)
        _append_check(checks, f"artifact:{name}:recorded_exists", f"artifact_digest.{name}.exists", True, row["expected_exists"], "Artifact must be recorded as present.")
        _append_check(checks, f"artifact:{name}:current_exists", f"artifact_digest.{name}.path", True, row["actual_exists"], "Recorded artifact path must still exist.")
        _append_check(checks, f"artifact:{name}:size", f"artifact_digest.{name}.size_bytes", row["expected_size_bytes"], row["actual_size_bytes"], "Recorded artifact size must match the current file.")
        _append_check(checks, f"artifact:{name}:sha256_shape", f"artifact_digest.{name}.sha256", "64 lowercase hex", _sha256_shape(row["expected_sha256"]), "Recorded SHA-256 must be a stable 64-character lowercase hex digest.")
        _append_check(checks, f"artifact:{name}:sha256", f"artifact_digest.{name}.sha256", row["expected_sha256"], row["actual_sha256"], "Recorded artifact digest must match the current file.")
    return rows


def _commands_by_name(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    commands = plan.get("commands")
    if not isinstance(commands, list):
        return {}
    return {str(item.get("name")): dict(item) for item in commands if isinstance(item, dict)}


def _append_check(
    checks: list[dict[str, Any]],
    check_id: str,
    target: str,
    expected: Any,
    actual: Any,
    detail: str,
) -> None:
    checks.append(
        {
            "id": check_id,
            "target": target,
            "expected": expected,
            "actual": actual,
            "status": "pass" if actual == expected else "fail",
            "detail": detail,
        }
    )


def _actual_digest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "size_bytes": 0, "sha256": ""}
    data = path.read_bytes()
    return {"exists": True, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _missing_actual() -> dict[str, Any]:
    return {"exists": False, "size_bytes": 0, "sha256": ""}


def _artifact_matches(row: dict[str, Any]) -> bool:
    return (
        row.get("expected_exists") is True
        and row.get("actual_exists") is True
        and row.get("expected_size_bytes") == row.get("actual_size_bytes")
        and _sha256_shape(str(row.get("expected_sha256") or "")) == "64 lowercase hex"
        and row.get("expected_sha256") == row.get("actual_sha256")
    )


def _sha256_shape(value: str) -> str:
    return "64 lowercase hex" if SHA256_RE.match(value) else "invalid"


def _issue_from_check(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": "plan_check_failed",
        "severity": "blocker",
        "target": check.get("target"),
        "detail": f"{check.get('id')} expected {check.get('expected')!r}, got {check.get('actual')!r}",
    }


def _check_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('id'))}</td>"
        f"<td>{_e(item.get('target'))}</td>"
        f"<td>{_e(item.get('expected'))}</td>"
        f"<td>{_e(item.get('actual'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('detail'))}</td>"
        "</tr>"
    )


def _artifact_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('name'))}</td>"
        f"<td>{_e(item.get('status'))}</td>"
        f"<td>{_e(item.get('actual_size_bytes'))}</td>"
        f"<td>{_e(item.get('actual_sha256'))}</td>"
        f"<td>{_e(item.get('path'))}</td>"
        "</tr>"
    )


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _int_or_zero(value: Any) -> int:
    if isinstance(value, bool) or value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1120px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #265f73; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 16px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #eef3f6; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()


if __name__ == "__main__":
    main()
