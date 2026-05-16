from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from minigpt.maturity_artifacts import (
    render_maturity_summary_html,
    render_maturity_summary_markdown,
    write_maturity_summary_csv,
    write_maturity_summary_html,
    write_maturity_summary_json,
    write_maturity_summary_markdown,
    write_maturity_summary_outputs,
)


@dataclass(frozen=True)
class CapabilitySpec:
    key: str
    title: str
    versions: tuple[int, ...]
    target_level: int
    evidence: str
    next_step: str


CAPABILITY_SPECS = (
    CapabilitySpec(
        "model_core",
        "Model Core",
        (1, 2, 3, 4, 5, 6, 7, 10),
        4,
        "Tokenizer, GPT blocks, training artifacts, BPE, attention, prediction, chat wrapper, model reports, and sampling controls.",
        "Train larger baselines and compare scale/quality changes on fixed benchmark prompts.",
    ),
    CapabilitySpec(
        "data_reproducibility",
        "Data And Reproducibility",
        (13, 14, 15, 16, 35, 36),
        4,
        "Dataset preparation, run manifests, dataset quality checks, eval suites, benchmark metadata, and dataset version manifests.",
        "Add dataset cards and stable train/validation/test split policies for larger corpora.",
    ),
    CapabilitySpec(
        "evaluation_benchmarks",
        "Evaluation Benchmarks",
        (16, 28, 35, 37, 43, 44, 45, 46, 47),
        4,
        "Fixed prompt eval, generation quality, baseline comparison, pair batch, pair trend, dashboard links, registry links, and delta leaders.",
        "Consolidate eval and pair outputs into one benchmark suite with task-level pass/fail scoring.",
    ),
    CapabilitySpec(
        "local_inference",
        "Local Inference And Playground",
        (11, 12, 38, 39, 40, 41, 42, 55, 56, 57, 58, 59, 60),
        5,
        "Static playground, local API, safety profiles, checkpoint selector, checkpoint comparison, side-by-side generation, saved pair artifacts, streaming, request history, row detail JSON, and request history summaries.",
        "Connect request history stability summaries to audit/release handoff when local serving evidence becomes release-relevant.",
    ),
    CapabilitySpec(
        "registry_reporting",
        "Registry And Reporting",
        (8, 9, 17, 18, 19, 20, 21, 22, 23, 24, 46, 47, 64),
        5,
        "Dashboard, run comparison, registry HTML, saved views, annotations, leaderboards, experiment/model cards, pair report registry views, and release readiness trend tracking.",
        "Feed release readiness trend context into maturity review and release summaries.",
    ),
    CapabilitySpec(
        "release_governance",
        "Release Governance",
        (25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 61, 62, 63),
        5,
        "Project audit, release bundle, release gate, generation quality policy, policy profiles, profile comparison, deltas, configurable baselines, request-history audit gates, readiness dashboard, and readiness comparison.",
        "Use release readiness trend context to guide maturity and release review instead of adding more gate variants.",
    ),
    CapabilitySpec(
        "documentation_evidence",
        "Documentation And Evidence",
        (1, 8, 13, 23, 32, 35, 45, 46, 47, 48, 64, 65),
        5,
        "Version tags, README history, code explanations, archived screenshots, browser checks, maturity summary, and release trend evidence.",
        "Keep future code explanations tied to concrete evidence and summarize phases instead of expanding every small link change.",
    ),
    CapabilitySpec(
        "project_synthesis",
        "Project Synthesis",
        (23, 24, 25, 26, 27, 37, 46, 47, 48, 60, 61, 62, 63, 64, 65),
        4,
        "Experiment cards, model cards, audit/bundle/gate outputs, baseline comparison, request-history context, release readiness context, registry trend tracking, and maturity summary.",
        "Use maturity trend context to choose the next real capability: larger data, benchmark hardening, or serving review.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_maturity_summary(
    project_root: str | Path,
    *,
    title: str = "MiniGPT project maturity summary",
    generated_at: str | None = None,
    registry_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    published_versions = _discover_published_versions(root)
    archive_versions = _discover_archive_versions(root)
    explanation_versions = _discover_explanation_versions(root)
    registry = _read_json(Path(registry_path)) if registry_path is not None else _read_json(root / "runs" / "registry" / "registry.json")
    request_history_summary = (
        _read_json(Path(request_history_summary_path))
        if request_history_summary_path is not None
        else _read_json(root / "runs" / "request-history-summary" / "request_history_summary.json")
    )
    capabilities = [_capability_row(spec, published_versions) for spec in CAPABILITY_SPECS]
    registry_context = _registry_context(registry)
    release_readiness_context = _release_readiness_context(registry)
    request_history_context = _request_history_context(request_history_summary)
    summary = _summary(
        published_versions,
        archive_versions,
        explanation_versions,
        capabilities,
        registry,
        request_history_summary,
        release_readiness_context,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "project_root": str(root),
        "summary": summary,
        "capabilities": capabilities,
        "phase_timeline": _phase_timeline(published_versions),
        "registry_context": registry_context,
        "release_readiness_context": release_readiness_context,
        "request_history_context": request_history_context,
        "recommendations": _recommendations(capabilities, registry, request_history_summary, release_readiness_context),
    }


def _discover_published_versions(root: Path) -> list[int]:
    readme = root / "README.md"
    if not readme.exists():
        return []
    versions = {int(match.group(1)) for match in re.finditer(r"\bv(\d+)\.0\.0\b", readme.read_text(encoding="utf-8-sig"))}
    return sorted(versions)


def _discover_archive_versions(root: Path) -> list[int]:
    versions = set()
    for archive_root in [root / "a", root / "b", root / "c"]:
        if not archive_root.exists():
            continue
        for child in archive_root.iterdir():
            if child.is_dir() and child.name.isdigit():
                versions.add(int(child.name))
    return sorted(versions)


def _discover_explanation_versions(root: Path) -> list[int]:
    versions = set()
    for directory in root.iterdir():
        if not directory.is_dir() or not directory.name.startswith("代码讲解记录"):
            continue
        for path in directory.glob("*.md"):
            match = re.search(r"-v(\d+)-", path.name)
            if match:
                versions.add(int(match.group(1)))
    return sorted(versions)


def _capability_row(spec: CapabilitySpec, published_versions: list[int]) -> dict[str, Any]:
    published = set(published_versions)
    covered = [version for version in spec.versions if version in published]
    missing = [version for version in spec.versions if version not in published]
    ratio = len(covered) / len(spec.versions) if spec.versions else 0.0
    maturity_level = min(spec.target_level, max(1, round(ratio * spec.target_level))) if ratio else 0
    status = "pass" if ratio >= 0.9 else "warn" if ratio >= 0.5 else "fail"
    return {
        "key": spec.key,
        "title": spec.title,
        "status": status,
        "maturity_level": maturity_level,
        "target_level": spec.target_level,
        "score_percent": round(ratio * 100, 1),
        "covered_count": len(covered),
        "target_count": len(spec.versions),
        "covered_versions": covered,
        "missing_versions": missing,
        "evidence": spec.evidence,
        "next_step": spec.next_step,
    }


def _summary(
    published_versions: list[int],
    archive_versions: list[int],
    explanation_versions: list[int],
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    release_readiness_context: dict[str, Any],
) -> dict[str, Any]:
    average = 0.0
    if capabilities:
        average = round(sum(float(item.get("maturity_level") or 0) for item in capabilities) / len(capabilities), 2)
    statuses = [str(item.get("status")) for item in capabilities]
    overall = "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"
    if overall == "pass" and release_readiness_context.get("trend_status") in {"regressed", "ci-regressed"}:
        overall = "warn"
    return {
        "current_version": max(published_versions) if published_versions else None,
        "published_version_count": len(published_versions),
        "archive_version_count": len(archive_versions),
        "explanation_version_count": len(explanation_versions),
        "average_maturity_level": average,
        "overall_status": overall,
        "registry_runs": _pick(registry, "run_count"),
        "release_readiness_trend_status": release_readiness_context.get("trend_status"),
        "release_readiness_delta_count": release_readiness_context.get("delta_count"),
        "release_readiness_regressed_count": release_readiness_context.get("regressed_count"),
        "release_readiness_improved_count": release_readiness_context.get("improved_count"),
        "release_readiness_ci_workflow_regression_count": release_readiness_context.get("ci_workflow_regression_count"),
        "release_readiness_ci_workflow_status_changed_count": release_readiness_context.get("ci_workflow_status_changed_count"),
        "release_readiness_max_ci_workflow_failed_check_delta": release_readiness_context.get("max_abs_ci_workflow_failed_check_delta"),
        "request_history_status": _nested_pick(request_history_summary, "summary", "status"),
        "request_history_records": _nested_pick(request_history_summary, "summary", "total_log_records"),
        "request_history_timeout_rate": _nested_pick(request_history_summary, "summary", "timeout_rate"),
        "request_history_error_rate": _nested_pick(request_history_summary, "summary", "error_rate"),
    }


def _phase_timeline(published_versions: list[int]) -> list[dict[str, Any]]:
    published = set(published_versions)
    phases = [
        ("v1-v12", "MiniGPT learning core", range(1, 13)),
        ("v13-v24", "Data, registry, and cards", range(13, 25)),
        ("v25-v34", "Release governance", range(25, 35)),
        ("v35-v47", "Evaluation benchmark and pair reports", range(35, 48)),
        ("v48-v60", "Project maturity and local inference hardening", range(48, 61)),
        ("v61-v65", "Release readiness and maturity trend context", range(61, 66)),
    ]
    rows = []
    for versions, title, version_range in phases:
        expected = list(version_range)
        covered = [version for version in expected if version in published]
        ratio = len(covered) / len(expected) if expected else 0
        rows.append(
            {
                "versions": versions,
                "title": title,
                "covered_count": len(covered),
                "target_count": len(expected),
                "status": "pass" if ratio >= 0.9 else "warn" if ratio > 0 else "pending",
            }
        )
    return rows


def _registry_context(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "available": False,
            "run_count": None,
            "pair_delta_cases": None,
            "pair_report_counts": {},
        }
    pair_delta = _dict(registry.get("pair_delta_summary"))
    return {
        "available": True,
        "run_count": registry.get("run_count"),
        "quality_counts": registry.get("quality_counts") if isinstance(registry.get("quality_counts"), dict) else {},
        "generation_quality_counts": registry.get("generation_quality_counts") if isinstance(registry.get("generation_quality_counts"), dict) else {},
        "pair_report_counts": registry.get("pair_report_counts") if isinstance(registry.get("pair_report_counts"), dict) else {},
        "pair_delta_cases": pair_delta.get("case_count"),
        "pair_delta_max_generated": pair_delta.get("max_abs_generated_char_delta"),
    }


def _release_readiness_context(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "available": False,
            "trend_status": None,
            "comparison_counts": {},
            "delta_count": None,
            "run_count": None,
            "regressed_count": None,
            "improved_count": None,
            "panel_changed_count": None,
            "changed_panel_delta_count": None,
            "max_abs_status_delta": None,
            "ci_workflow_regression_count": None,
            "ci_workflow_status_changed_count": None,
            "max_abs_ci_workflow_failed_check_delta": None,
        }
    counts = registry.get("release_readiness_comparison_counts")
    delta_summary = _dict(registry.get("release_readiness_delta_summary"))
    context = {
        "available": bool(delta_summary) or isinstance(counts, dict),
        "comparison_counts": counts if isinstance(counts, dict) else {},
        "delta_count": delta_summary.get("delta_count"),
        "run_count": delta_summary.get("run_count"),
        "regressed_count": delta_summary.get("regressed_count"),
        "improved_count": delta_summary.get("improved_count"),
        "panel_changed_count": delta_summary.get("panel_changed_count"),
        "same_count": delta_summary.get("same_count"),
        "changed_panel_delta_count": delta_summary.get("changed_panel_delta_count"),
        "max_abs_status_delta": delta_summary.get("max_abs_status_delta"),
        "ci_workflow_regression_count": delta_summary.get("ci_workflow_regression_count"),
        "ci_workflow_status_changed_count": delta_summary.get("ci_workflow_status_changed_count"),
        "max_abs_ci_workflow_failed_check_delta": delta_summary.get("max_abs_ci_workflow_failed_check_delta"),
    }
    context["trend_status"] = _release_readiness_trend_status(context)
    return context


def _release_readiness_trend_status(context: dict[str, Any]) -> str | None:
    if not context.get("available"):
        return None
    if int(context.get("regressed_count") or 0) > 0:
        return "regressed"
    if int(context.get("ci_workflow_regression_count") or 0) > 0:
        return "ci-regressed"
    if int(context.get("improved_count") or 0) > 0:
        return "improved"
    if int(context.get("panel_changed_count") or 0) > 0 or int(context.get("changed_panel_delta_count") or 0) > 0:
        return "panel-changed"
    if int(context.get("delta_count") or 0) > 0:
        return "stable"
    counts = _dict(context.get("comparison_counts"))
    if counts:
        return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))
    return None


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {
            "available": False,
            "status": None,
            "total_log_records": None,
            "timeout_rate": None,
            "bad_request_rate": None,
            "error_rate": None,
        }
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "ok_count": summary.get("ok_count"),
        "timeout_count": summary.get("timeout_count"),
        "bad_request_count": summary.get("bad_request_count"),
        "error_count": summary.get("error_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "stream_request_count": summary.get("stream_request_count"),
        "pair_request_count": summary.get("pair_request_count"),
        "unique_checkpoint_count": summary.get("unique_checkpoint_count"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _recommendations(
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    release_readiness_context: dict[str, Any],
) -> list[str]:
    recs = [
        "Treat v48 as a phase summary: avoid continuing to split links/trends/dashboard unless the change improves evaluation quality.",
        "Next high-value step: consolidate eval suite, generation quality, pair batch, and pair delta leaders into one benchmark scoring suite.",
        "Use the maturity matrix to explain the project as a learning AI engineering artifact, not as a production-grade model service.",
    ]
    weak = [item for item in capabilities if item.get("status") != "pass"]
    if weak:
        recs.append("Revisit weaker areas first: " + ", ".join(str(item.get("title")) for item in weak[:3]) + ".")
    if not isinstance(registry, dict):
        recs.append("Generate a fresh registry before final portfolio review so the maturity summary can include live run counts.")
    if not release_readiness_context.get("available"):
        recs.append("Generate a registry with release readiness comparison outputs so maturity review can include release quality trend context.")
    elif int(release_readiness_context.get("regressed_count") or 0) > 0:
        recs.append("Review release readiness regressions before presenting the project as release-stable; maturity status is downgraded to review.")
    elif int(release_readiness_context.get("ci_workflow_regression_count") or 0) > 0:
        recs.append("Review CI workflow hygiene regressions before presenting the project as release-stable; maturity status is downgraded to review.")
    elif int(release_readiness_context.get("improved_count") or 0) > 0:
        recs.append("Keep release readiness comparison evidence in the registry so improvement history remains visible during maturity review.")
    if not isinstance(request_history_summary, dict):
        recs.append("Generate request_history_summary.json before local serving review so maturity context includes recent inference stability.")
    else:
        request_summary = _dict(request_history_summary.get("summary"))
        if request_summary.get("status") not in {"pass", "empty"}:
            recs.append("Review request history summary warnings before using the playground session as stable local inference evidence.")
    return recs


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _nested_pick(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
