from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

STABLE_OUTPUT_STEM = "project_docs_readability"
LEGACY_V1131_OUTPUT_STEM = "project_docs_readability_v1131"

COMMON_MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u9225",
    "\u95ab",
    "\u93c2\u56e8",
    "\u6d60\uff47",
    "\u813f",
    "\u87ff",
)

DOC_TARGETS = [
    {
        "path": "docs/overview.md",
        "title": "# MiniGPT Project Overview",
        "required_terms": ["MiniGPT", "AI governance", "publication receipt"],
    },
    {
        "path": "docs/architecture-map.md",
        "title": "# MiniGPT Architecture Map",
        "required_terms": ["owner class", "governance", "core"],
    },
    {
        "path": "docs/module-inventory.md",
        "title": "# MiniGPT Module Inventory",
        "required_terms": [
            "Owner class",
            "compatibility path",
            "Normalized Owner Packages",
            "minigpt.governance",
            "recursively scans",
        ],
    },
    {
        "path": "docs/public-api.md",
        "title": "# MiniGPT Public API Policy",
        "required_terms": [
            "Tier 1",
            "compatibility",
            "owner packages",
            "flat modules",
            "minigpt.evaluation.prediction",
            "minigpt.serving.chat",
            "minigpt.reports.utils",
            "Root Facade Export Budget",
            "_root_exports.py",
            "_root_*exports*.py",
        ],
    },
    {
        "path": "docs/normalization-roadmap.md",
        "title": "# MiniGPT Normalization Roadmap",
        "required_terms": ["Current Phase", "owner packages", "Next Actions"],
    },
    {
        "path": "docs/engineering-workflow.md",
        "title": "# MiniGPT Engineering Workflow",
        "required_terms": ["unittest", "CI", "owner packages"],
    },
    {
        "path": "docs/normalization-guard.md",
        "title": "# MiniGPT Normalization Guard",
        "required_terms": [
            "FOCUSED_TEST_MODULES",
            "tests.test_script_bootstrap",
            "tests.test_script_bootstrap_helpers",
            "tests.test_script_surface_registry",
            "tests.test_script_cli_contracts",
            "tests.test_report_utils",
            "tests.test_report_utils_helpers",
            "tests.test_active_cli_coverage",
            "tests.test_active_cli_behavior",
            "tests.test_model_cli_behavior",
            "tests.test_serving_cli_behavior",
            "tests.test_report_cli_behavior",
            "tests.test_governance_cli_behavior",
            "tests.test_governance_extended_cli_behavior",
            "ACTIVE_CLI_BEHAVIOR_COVERAGE",
            "tests.test_test_coverage_report",
            "transitional package files stay small",
            "facade-only package initializers",
            "hidden re-export drift",
            "facade-only transitional submodules",
            "explicit imports aligned with `__all__`",
            "submodule `__all__` tables",
        ],
    },
    {
        "path": "docs/script-entrypoints.md",
        "title": "# MiniGPT Script Entrypoints",
        "required_terms": [
            "check_engineering_health.py",
            "stable maintainer",
            "Current Maintained Script Surface",
            "CURRENT_MAINTAINED_SCRIPT_ENTRYPOINTS",
            "FOUNDATION_ACTIVE_CLI_ENTRYPOINTS",
            "REPORT_ACTIVE_CLI_ENTRYPOINTS",
            "GOVERNANCE_ACTIVE_CLI_ENTRYPOINTS",
            "Normalized Active CLIs",
            "ACTIVE_CLI_BEHAVIOR_COVERAGE",
            "Promotion Rule",
            "Text Hygiene",
            "import-safe",
            "root `minigpt` facade",
            "mojibake",
            "historical",
            "SCRIPT_ENTRYPOINT_SURFACES",
            "SCRIPT_SUPPORT_MODULES",
            "repository-relative POSIX `.py` paths",
            "not runnable maintainer entrypoints",
            "support module `__all__`",
            "Support modules are also import-safe",
        ],
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

FRONT_DOOR_TARGETS = [
    {
        "path": "START_HERE.md",
        "title": "# Start Here: MiniGPT From Scratch",
        "required_terms": [
            "docs/architecture-map.md",
            "docs/engineering-workflow.md",
            "docs/normalization-guard.md",
            "docs/script-entrypoints.md",
            "scripts/check_normalization_guard.py",
        ],
        "forbidden_terms": COMMON_MOJIBAKE_MARKERS,
    },
    {
        "path": "docs/README.md",
        "title": "# MiniGPT Documentation Map",
        "required_terms": [
            "architecture-map.md",
            "engineering-workflow.md",
            "normalization-roadmap.md",
            "normalization-guard.md",
            "script-entrypoints.md",
        ],
        "forbidden_terms": COMMON_MOJIBAKE_MARKERS,
    },
]


def build_project_docs_readability_report(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    readme = project_root / "README.md"
    readme_text = _read_text(readme)
    doc_rows = [_doc_row(project_root, readme_text, target) for target in DOC_TARGETS]
    front_door_rows = [_front_door_row(project_root, target) for target in FRONT_DOOR_TARGETS]
    rows = doc_rows + front_door_rows
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
            "row_count": len(rows),
            "ready_row_count": len(rows) - len(failed_rows),
            "doc_target_count": len(DOC_TARGETS),
            "ready_doc_count": sum(1 for row in doc_rows if row["status"] == "pass"),
            "missing_doc_count": sum(1 for row in doc_rows if row["exists"] is False),
            "missing_readme_link_count": sum(1 for row in doc_rows if row["readme_link_present"] is False),
            "front_door_target_count": len(FRONT_DOOR_TARGETS),
            "front_door_ready_count": sum(1 for row in front_door_rows if row["status"] == "pass"),
            "front_door_failed_count": sum(1 for row in front_door_rows if row["status"] != "pass"),
            "forbidden_term_hit_count": sum(len(row["forbidden_term_hits"]) for row in front_door_rows),
            "failed_count": len(failed_rows),
            "docs_root": "docs",
            "readme_keeps_history": True,
        },
        "rows": rows,
        "recommendations": [
            "Use README as a navigation entry and keep deep explanations in docs/.",
            "Keep START_HERE.md and docs/README.md as clean front-door navigation files.",
            "Keep publication receipt concepts in docs/publication-receipts.md instead of repeating them in every version note.",
            "Keep no-promotion language centralized so governance reports are not confused with model-quality claims.",
        ],
        "csv_fieldnames": [
            "row_type",
            "path",
            "exists",
            "readme_link_present",
            "heading_present",
            "required_terms_present",
            "forbidden_terms_absent",
            "status",
            "recommendation",
        ],
    }


def write_project_docs_readability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
    *,
    stem: str = STABLE_OUTPUT_STEM,
) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=stem,
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
        "row_type": "doc_target",
        "path": path,
        "exists": exists,
        "readme_link_present": readme_link_present,
        "heading_present": heading_present,
        "required_terms_present": not missing_terms,
        "forbidden_terms_absent": True,
        "missing_terms": missing_terms,
        "forbidden_term_hits": [],
        "status": status,
        "recommendation": "ready" if status == "pass" else "repair docs target or README link",
    }


def _front_door_row(root: Path, target: dict[str, Any]) -> dict[str, Any]:
    path = str(target["path"])
    file_path = root / path
    text = _read_text(file_path)
    required_terms = [str(term) for term in target["required_terms"]]
    forbidden_terms = [str(term) for term in target["forbidden_terms"]]
    missing_terms = [term for term in required_terms if term not in text]
    forbidden_hits = [term for term in forbidden_terms if term in text]
    exists = file_path.is_file()
    heading_present = str(target["title"]) in text
    status = "pass" if exists and heading_present and not missing_terms and not forbidden_hits else "fail"
    return {
        "row_type": "front_door",
        "path": path,
        "exists": exists,
        "readme_link_present": True,
        "heading_present": heading_present,
        "required_terms_present": not missing_terms,
        "forbidden_terms_absent": not forbidden_hits,
        "missing_terms": missing_terms,
        "forbidden_term_hits": forbidden_hits,
        "status": status,
        "recommendation": "ready" if status == "pass" else "repair front-door navigation or mojibake",
    }


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8-sig")


__all__ = [
    "COMMON_MOJIBAKE_MARKERS",
    "DOC_TARGETS",
    "FRONT_DOOR_TARGETS",
    "LEGACY_V1131_OUTPUT_STEM",
    "STABLE_OUTPUT_STEM",
    "build_project_docs_readability_report",
    "resolve_exit_code",
    "write_project_docs_readability_outputs",
]
