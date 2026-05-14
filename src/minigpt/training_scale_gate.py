from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell as _csv_value,
    display_command as _display_command,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_json_payload,
)


POLICY_PROFILES: dict[str, dict[str, Any]] = {
    "review": {
        "min_char_count": 200,
        "small_corpus_status": "warn",
        "tiny_status": "warn",
        "max_warning_count": 5,
        "quality_warning_status": "warn",
        "min_variant_count": 1,
        "max_variant_count": 4,
        "max_token_budget": 2_000_000,
        "max_corpus_pass_estimate": 500.0,
        "budget_status": "warn",
        "corpus_pass_status": "warn",
    },
    "standard": {
        "min_char_count": 2_000,
        "small_corpus_status": "fail",
        "tiny_status": "fail",
        "max_warning_count": 0,
        "quality_warning_status": "fail",
        "min_variant_count": 1,
        "max_variant_count": 4,
        "max_token_budget": 2_000_000,
        "max_corpus_pass_estimate": 150.0,
        "budget_status": "fail",
        "corpus_pass_status": "warn",
    },
    "strict": {
        "min_char_count": 20_000,
        "small_corpus_status": "fail",
        "tiny_status": "fail",
        "max_warning_count": 0,
        "quality_warning_status": "fail",
        "min_variant_count": 2,
        "max_variant_count": 3,
        "max_token_budget": 5_000_000,
        "max_corpus_pass_estimate": 50.0,
        "budget_status": "fail",
        "corpus_pass_status": "fail",
    },
}


def load_training_scale_plan(path: str | Path) -> dict[str, Any]:
    return _dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def build_training_scale_gate(
    plan: dict[str, Any],
    *,
    plan_path: str | Path | None = None,
    profile: str = "review",
    policy_overrides: dict[str, Any] | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale gate",
) -> dict[str, Any]:
    policy = _policy(profile, policy_overrides)
    checks = _build_checks(plan, policy)
    summary = _status_summary(checks)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "profile": profile,
        "policy": policy,
        "plan_path": None if plan_path is None else str(plan_path),
        "plan_summary": _plan_summary(plan),
        "overall_status": summary["overall_status"],
        "pass_count": summary["pass_count"],
        "warn_count": summary["warn_count"],
        "fail_count": summary["fail_count"],
        "checks": checks,
        "batch": _dict(plan.get("batch")),
        "recommendations": _recommendations(summary["overall_status"], checks, plan),
    }


def write_training_scale_gate_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_gate_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["code", "status", "message", "recommendation", "details"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for check in _list_of_dicts(report.get("checks")):
            writer.writerow(
                {
                    "code": check.get("code"),
                    "status": check.get("status"),
                    "message": check.get("message"),
                    "recommendation": check.get("recommendation"),
                    "details": _csv_value(check.get("details", {})),
                }
            )


def render_training_scale_gate_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("plan_summary"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale gate')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Profile: `{report.get('profile')}`",
        f"- Status: `{report.get('overall_status')}`",
        f"- Plan: `{report.get('plan_path')}`",
        f"- Dataset: `{summary.get('dataset_name')}` / `{summary.get('version_prefix')}`",
        f"- Scale: `{summary.get('scale_tier')}`",
        f"- Characters: `{summary.get('char_count')}`",
        f"- Variants: `{summary.get('variant_count')}`",
        f"- Warnings: `{summary.get('warning_count')}`",
        "",
        "## Checks",
        "",
        "| Status | Code | Message | Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for check in _list_of_dicts(report.get("checks")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(check.get("status")),
                    _md(check.get("code")),
                    _md(check.get("message")),
                    _md(check.get("recommendation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    batch = _dict(report.get("batch"))
    if batch.get("command"):
        lines.extend(["", "## Batch Command", "", f"`{_display_command(batch.get('command'))}`"])
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_gate_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_gate_markdown(report), encoding="utf-8")


def render_training_scale_gate_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("plan_summary"))
    stats = [
        ("Status", report.get("overall_status")),
        ("Profile", report.get("profile")),
        ("Pass", report.get("pass_count")),
        ("Warn", report.get("warn_count")),
        ("Fail", report.get("fail_count")),
        ("Scale", summary.get("scale_tier")),
        ("Chars", summary.get("char_count")),
        ("Variants", summary.get("variant_count")),
    ]
    batch = _dict(report.get("batch"))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale gate'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale gate'))}</h1><p>{_e(summary.get('dataset_name'))} / {_e(summary.get('version_prefix'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _checks_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            _batch_section(batch),
            "<footer>Generated by MiniGPT training scale gate.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_gate_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_gate_html(report), encoding="utf-8")


def write_training_scale_gate_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_gate.json",
        "csv": root / "training_scale_gate.csv",
        "markdown": root / "training_scale_gate.md",
        "html": root / "training_scale_gate.html",
    }
    write_training_scale_gate_json(report, paths["json"])
    write_training_scale_gate_csv(report, paths["csv"])
    write_training_scale_gate_markdown(report, paths["markdown"])
    write_training_scale_gate_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _policy(profile: str, overrides: dict[str, Any] | None) -> dict[str, Any]:
    if profile not in POLICY_PROFILES:
        choices = ", ".join(sorted(POLICY_PROFILES))
        raise ValueError(f"unknown profile {profile!r}; choose one of: {choices}")
    policy = dict(POLICY_PROFILES[profile])
    policy.update(dict(overrides or {}))
    policy["profile"] = profile
    return policy


def _build_checks(plan: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    variants = _list_of_dicts(plan.get("variants"))
    matrix = _list_of_dicts(plan.get("variant_matrix"))
    char_count = _int(dataset.get("char_count"))
    warning_count = _int(dataset.get("warning_count"))
    scale_tier = str(dataset.get("scale_tier") or "unknown")
    baseline = str(batch.get("baseline") or "")
    variant_names = {str(item.get("name") or "") for item in variants}
    checks = [
        _check(
            "plan_schema",
            "pass" if int(plan.get("schema_version") or 0) >= 1 and dataset else "fail",
            "Plan has a supported schema and dataset block.",
            "Regenerate the v70 training scale plan before running the batch.",
            {"schema_version": plan.get("schema_version"), "has_dataset": bool(dataset)},
        ),
        _check(
            "source_count",
            "pass" if _int(dataset.get("source_count")) > 0 else "fail",
            f"Plan references {_int(dataset.get('source_count'))} source files.",
            "Provide at least one .txt source file or directory.",
            {"source_count": dataset.get("source_count")},
        ),
        _check(
            "dataset_fingerprint",
            "pass" if dataset.get("fingerprint") else "warn",
            "Dataset fingerprint is present.",
            "Regenerate the scale plan with dataset preparation metadata.",
            {"fingerprint": dataset.get("fingerprint")},
        ),
        _check(
            "min_char_count",
            "pass" if char_count >= int(policy["min_char_count"]) else str(policy["small_corpus_status"]),
            f"Corpus has {char_count} characters; policy minimum is {policy['min_char_count']}.",
            "Collect more training text before treating results as model capability evidence.",
            {"char_count": char_count, "min_char_count": policy["min_char_count"]},
        ),
        _check(
            "tiny_corpus",
            str(policy["tiny_status"]) if scale_tier == "tiny" else "pass",
            f"Scale tier is {scale_tier}.",
            "Use tiny-corpus runs only as pipeline smoke evidence.",
            {"scale_tier": scale_tier},
        ),
        _check(
            "quality_warnings",
            "pass" if warning_count <= int(policy["max_warning_count"]) else str(policy["quality_warning_status"]),
            f"Dataset has {warning_count} quality warnings; policy maximum is {policy['max_warning_count']}.",
            "Review data quality issues before executing longer variants.",
            {"warning_count": warning_count, "max_warning_count": policy["max_warning_count"]},
        ),
        _check(
            "variant_count",
            _variant_count_status(len(variants), policy),
            f"Plan has {len(variants)} variants; policy range is {policy['min_variant_count']}..{policy['max_variant_count']}.",
            "Keep the matrix small enough to review and large enough to compare.",
            {"variant_count": len(variants), "min": policy["min_variant_count"], "max": policy["max_variant_count"]},
        ),
        _check(
            "baseline_variant",
            "pass" if baseline and baseline in variant_names else "fail",
            f"Baseline variant is {baseline or '<missing>'}.",
            "Set batch.baseline to one of the planned variant names.",
            {"baseline": baseline, "variant_names": sorted(variant_names)},
        ),
        _check(
            "batch_handoff",
            "pass" if batch.get("variants_path") and batch.get("command") else "fail",
            "Batch handoff path and command are present.",
            "Regenerate the scale plan so it includes variants_path and batch command.",
            {"variants_path": batch.get("variants_path"), "has_command": bool(batch.get("command"))},
        ),
        _check(
            "variant_dataset_versions",
            "pass" if variants and all(item.get("dataset_version") for item in variants) else "fail",
            "Every variant has a dataset_version.",
            "Give each variant a stable dataset_version before executing the batch.",
            {"missing": [item.get("name") for item in variants if not item.get("dataset_version")]},
        ),
        _budget_check(matrix, policy),
        _corpus_pass_check(matrix, policy),
    ]
    return checks


def _budget_check(matrix: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    max_row = _max_row(matrix, "token_budget")
    value = _float(max_row.get("token_budget")) if max_row else 0.0
    status = "pass" if max_row and value <= float(policy["max_token_budget"]) else str(policy["budget_status"])
    return _check(
        "token_budget",
        status,
        f"Largest token budget is {int(value)}; policy maximum is {policy['max_token_budget']}.",
        "Reduce max_iters, batch_size, or block_size before executing expensive variants.",
        {"variant": max_row.get("name") if max_row else None, "token_budget": value, "max_token_budget": policy["max_token_budget"]},
    )


def _corpus_pass_check(matrix: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    max_row = _max_row(matrix, "corpus_pass_estimate")
    value = _float(max_row.get("corpus_pass_estimate")) if max_row else 0.0
    status = "pass" if max_row and value <= float(policy["max_corpus_pass_estimate"]) else str(policy["corpus_pass_status"])
    return _check(
        "corpus_pass_estimate",
        status,
        f"Largest estimated corpus passes is {value}; policy maximum is {policy['max_corpus_pass_estimate']}.",
        "For tiny corpora, lower iterations or gather more data before trusting loss improvements.",
        {
            "variant": max_row.get("name") if max_row else None,
            "corpus_pass_estimate": value,
            "max_corpus_pass_estimate": policy["max_corpus_pass_estimate"],
        },
    )


def _check(code: str, status: str, message: str, recommendation: str, details: dict[str, Any]) -> dict[str, Any]:
    if status not in {"pass", "warn", "fail"}:
        raise ValueError(f"invalid check status: {status}")
    return {
        "code": code,
        "status": status,
        "message": message,
        "recommendation": recommendation,
        "details": details,
    }


def _status_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    fail_count = sum(1 for check in checks if check.get("status") == "fail")
    warn_count = sum(1 for check in checks if check.get("status") == "warn")
    pass_count = sum(1 for check in checks if check.get("status") == "pass")
    if fail_count:
        overall = "fail"
    elif warn_count:
        overall = "warn"
    else:
        overall = "pass"
    return {
        "overall_status": overall,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "pass_count": pass_count,
    }


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    dataset = _dict(plan.get("dataset"))
    return {
        "dataset_name": dataset.get("name"),
        "version_prefix": dataset.get("version_prefix"),
        "scale_tier": dataset.get("scale_tier"),
        "char_count": dataset.get("char_count"),
        "source_count": dataset.get("source_count"),
        "warning_count": dataset.get("warning_count"),
        "quality_status": dataset.get("quality_status"),
        "variant_count": len(_list_of_dicts(plan.get("variants"))),
        "baseline": _dict(plan.get("batch")).get("baseline"),
    }


def _recommendations(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> list[str]:
    if status == "pass":
        recommendations = ["The scale plan is ready to hand to the training portfolio batch runner."]
    elif status == "warn":
        recommendations = ["The scale plan can be used for smoke or review runs, but warnings should be read first."]
    else:
        recommendations = ["Do not execute the planned batch until failed checks are fixed or a looser profile is selected."]
    for check in checks:
        if check.get("status") in {"warn", "fail"}:
            recommendations.append(f"{check.get('code')}: {check.get('recommendation')}")
    command = _dict(plan.get("batch")).get("command")
    if command:
        recommendations.append(f"Batch command: {_display_command(command)}")
    return recommendations


def _variant_count_status(count: int, policy: dict[str, Any]) -> str:
    if count < int(policy["min_variant_count"]):
        return "fail"
    if count > int(policy["max_variant_count"]):
        return "warn"
    return "pass"


def _max_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    if not rows:
        return {}
    return max(rows, key=lambda row: _float(row.get(key)))


def _checks_table(report: dict[str, Any]) -> str:
    rows = []
    for check in _list_of_dicts(report.get("checks")):
        status = str(check.get("status") or "")
        rows.append(
            f'<tr class="{_e(status)}">'
            f"<td>{_e(status)}</td>"
            f"<td>{_e(check.get('code'))}</td>"
            f"<td>{_e(check.get('message'))}</td>"
            f"<td>{_e(check.get('recommendation'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Checks</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Status</th><th>Code</th><th>Message</th><th>Recommendation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _batch_section(batch: dict[str, Any]) -> str:
    if not batch:
        return ""
    return (
        "<section><h2>Batch Handoff</h2>"
        f"<p><strong>Variants:</strong> {_e(batch.get('variants_path'))}</p>"
        f"<pre>{_e(_display_command(batch.get('command')))}</pre>"
        "</section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    rows = "".join(f"<li>{_e(item)}</li>" for item in values)
    return f"<section><h2>{_e(title)}</h2><ul>{rows}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1120px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
tr.pass td:first-child { color: #047857; font-weight: 700; }
tr.warn td:first-child { color: #b45309; font-weight: 700; }
tr.fail td:first-child { color: #b91c1c; font-weight: 700; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
