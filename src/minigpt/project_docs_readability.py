from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

DOC_TARGETS = [
    {
        "path": "docs/overview.md",
        "title": "# MiniGPT Project Overview",
        "required_terms": ["MiniGPT", "AI governance", "publication receipt"],
    },
    {
        "path": "docs/model-training.md",
        "title": "# Model Training And Evaluation",
        "required_terms": ["training", "evaluation", "holdout"],
    },
    {
        "path": "docs/publication-receipts.md",
        "title": "# Publication Receipts",
        "required_terms": ["receipt", "contract check", "lookup-only"],
    },
    {
        "path": "docs/no-promotion-boundary.md",
        "title": "# No-Promotion Boundary",
        "required_terms": ["promotion", "model quality", "governance"],
    },
    {
        "path": "docs/versioned-artifacts.md",
        "title": "# Versioned Artifacts",
        "required_terms": ["f/", "screenshot", "artifact"],
    },
]


def build_project_docs_readability_report(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    readme = project_root / "README.md"
    readme_text = _read_text(readme)
    rows = [_doc_row(project_root, readme_text, target) for target in DOC_TARGETS]
    failed_rows = [row for row in rows if row["status"] != "pass"]
    status = "pass" if not failed_rows else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT project docs readability split v1131",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "project_docs_readability_split_ready" if status == "pass" else "repair_project_docs_readability_split",
        "summary": {
            "status": status,
            "decision": "project_docs_readability_split_ready" if status == "pass" else "repair_project_docs_readability_split",
            "doc_target_count": len(DOC_TARGETS),
            "ready_doc_count": len(rows) - len(failed_rows),
            "missing_doc_count": sum(1 for row in rows if row["exists"] is False),
            "missing_readme_link_count": sum(1 for row in rows if row["readme_link_present"] is False),
            "failed_count": len(failed_rows),
            "docs_root": "docs",
            "readme_keeps_history": True,
        },
        "rows": rows,
        "recommendations": [
            "Use README as a navigation entry and keep deep explanations in docs/.",
            "Keep publication receipt concepts in docs/publication-receipts.md instead of repeating them in every version note.",
            "Keep no-promotion language centralized so governance reports are not confused with model-quality claims.",
        ],
        "csv_fieldnames": ["path", "exists", "readme_link_present", "heading_present", "required_terms_present", "status", "recommendation"],
    }


def write_project_docs_readability_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem="project_docs_readability_v1131",
        row_title="Documentation Targets",
    )


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _doc_row(root: Path, readme_text: str, target: dict[str, Any]) -> dict[str, Any]:
    path = str(target["path"])
    file_path = root / path
    text = _read_text(file_path)
    required_terms = [str(term) for term in target["required_terms"]]
    missing_terms = [term for term in required_terms if term not in text]
    exists = file_path.is_file()
    heading_present = str(target["title"]) in text
    readme_link_present = f"({path})" in readme_text or f"]({path})" in readme_text
    status = "pass" if exists and heading_present and readme_link_present and not missing_terms else "fail"
    return {
        "path": path,
        "exists": exists,
        "readme_link_present": readme_link_present,
        "heading_present": heading_present,
        "required_terms_present": not missing_terms,
        "missing_terms": missing_terms,
        "status": status,
        "recommendation": "ready" if status == "pass" else "repair docs target or README link",
    }


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig")


__all__ = [
    "DOC_TARGETS",
    "build_project_docs_readability_report",
    "resolve_exit_code",
    "write_project_docs_readability_outputs",
]
