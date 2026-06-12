from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

TEMPLATE_PATH = Path("docs/publication-receipt-template.md")
REQUIRED_SECTIONS = [
    "# Publication Receipt Version Template",
    "## Version Scope",
    "## Required Files",
    "## Boundary Statements",
    "## Verification",
    "## Evidence Archive",
]
SCRIPT_LAYERS = {
    "publication": Path("scripts/publication"),
    "devtools": Path("scripts/devtools"),
}


def build_publication_receipt_template_report(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    template = project_root / TEMPLATE_PATH
    text = template.read_text(encoding="utf-8-sig") if template.is_file() else ""
    section_rows = [_section_row(text, section) for section in REQUIRED_SECTIONS]
    layer_rows = [_layer_row(project_root, name, path) for name, path in SCRIPT_LAYERS.items()]
    rows = section_rows + layer_rows
    failed_rows = [row for row in rows if row["status"] != "pass"]
    status = "pass" if not failed_rows else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT publication receipt template and script layers v1132",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "publication_receipt_template_ready" if status == "pass" else "repair_publication_receipt_template",
        "summary": {
            "status": status,
            "decision": "publication_receipt_template_ready" if status == "pass" else "repair_publication_receipt_template",
            "template_path": TEMPLATE_PATH.as_posix(),
            "required_section_count": len(REQUIRED_SECTIONS),
            "ready_section_count": sum(1 for row in section_rows if row["status"] == "pass"),
            "script_layer_count": len(SCRIPT_LAYERS),
            "ready_script_layer_count": sum(1 for row in layer_rows if row["status"] == "pass"),
            "failed_count": len(failed_rows),
            "template_ready": status == "pass",
        },
        "rows": rows,
        "recommendations": [
            "Use the template before adding a new receipt, check, index, or review version.",
            "Keep new publication scripts under scripts/publication/ and developer checks under scripts/devtools/.",
            "Keep no-promotion and lookup-only statements in the template so new versions do not invent fresh wording.",
        ],
        "csv_fieldnames": ["kind", "target", "exists", "status", "recommendation"],
    }


def write_publication_receipt_template_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem="publication_receipt_template_v1132",
        row_title="Template And Script Layer Checks",
    )


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _section_row(text: str, section: str) -> dict[str, Any]:
    exists = section in text
    return {
        "kind": "template-section",
        "target": section,
        "exists": exists,
        "status": "pass" if exists else "fail",
        "recommendation": "ready" if exists else "add missing template section",
    }


def _layer_row(root: Path, name: str, path: Path) -> dict[str, Any]:
    full_path = root / path
    exists = full_path.is_dir()
    return {
        "kind": "script-layer",
        "target": f"{name}:{path.as_posix()}",
        "exists": exists,
        "status": "pass" if exists else "fail",
        "recommendation": "ready" if exists else "create script layer directory",
    }


__all__ = [
    "REQUIRED_SECTIONS",
    "SCRIPT_LAYERS",
    "TEMPLATE_PATH",
    "build_publication_receipt_template_report",
    "resolve_exit_code",
    "write_publication_receipt_template_outputs",
]
