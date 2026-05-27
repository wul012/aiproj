from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def entry(
    safe_id: str,
    name: str,
    status: str,
    gate_status: str,
    suite_name: str | None = "standard-zh",
    *,
    include_handoff_suite_guard: bool = False,
    include_handoff_batch_review_context: bool = False,
    require_clean_batch_review: bool = False,
    clean_batch_review_status: str | None = None,
    batch_ci_regression_count: int = 0,
    batch_boundary_plan_regression_count: int = 0,
    batch_ci_regression_names: list[str] | None = None,
    batch_ci_regression_reason_counts: dict[str, int] | None = None,
    selected_batch_ci_regression_count: int = 0,
    selected_batch_boundary_plan_regression_count: int = 0,
    selected_batch_ci_regression_reason_counts: dict[str, int] | None = None,
    batch_suite_design_regression_count: int = 0,
    batch_suite_design_regression_names: list[str] | None = None,
    selected_batch_suite_design_regression_count: int = 0,
    selected_batch_suite_design_regression_names: list[str] | None = None,
    force_compare_ready: bool = False,
) -> dict:
    return {
        "safe_id": safe_id,
        "name": name,
        "status": status,
        "gate_status": gate_status,
        "suite_name": suite_name,
        "include_handoff_suite_guard": include_handoff_suite_guard,
        "include_handoff_batch_review_context": include_handoff_batch_review_context,
        "require_clean_batch_review": require_clean_batch_review,
        "clean_batch_review_status": clean_batch_review_status,
        "batch_ci_regression_count": batch_ci_regression_count,
        "batch_boundary_plan_regression_count": batch_boundary_plan_regression_count,
        "batch_ci_regression_names": batch_ci_regression_names or [],
        "batch_ci_regression_reason_counts": batch_ci_regression_reason_counts or {},
        "selected_batch_ci_regression_count": selected_batch_ci_regression_count,
        "selected_batch_boundary_plan_regression_count": selected_batch_boundary_plan_regression_count,
        "selected_batch_ci_regression_reason_counts": selected_batch_ci_regression_reason_counts
        or batch_ci_regression_reason_counts
        or {},
        "batch_suite_design_regression_count": batch_suite_design_regression_count,
        "batch_suite_design_regression_names": batch_suite_design_regression_names or [],
        "selected_batch_suite_design_regression_count": selected_batch_suite_design_regression_count,
        "selected_batch_suite_design_regression_names": selected_batch_suite_design_regression_names
        or batch_suite_design_regression_names
        or [],
        "force_compare_ready": force_compare_ready,
    }


def make_index_tree(root: Path, entries: list[dict], baseline_name: str | None = None) -> Path:
    index_dir = root / "promotion-index"
    promotions = []
    compare_names = []
    compare_paths = []
    for item in entries:
        run_path = root / "runs" / item["safe_id"] / "training_scale_run.json"
        write_json(run_path, scale_run(item["name"], item["gate_status"], item.get("suite_name")))
        rel_run_path = os.path.relpath(run_path, index_dir)
        promoted = item["status"] == "promoted"
        promotion = {
            "name": item["name"],
            "promotion_status": item["status"],
            "promoted_for_comparison": promoted,
            "training_scale_run_path": rel_run_path,
            "training_scale_run_exists": True,
        }
        clean_batch_review_status = item.get("clean_batch_review_status") or "review"
        if item.get("include_handoff_suite_guard"):
            promotion.update(
                {
                    "handoff_require_suite_consistency": True,
                    "handoff_suite_consistency": "consistent",
                    "handoff_suite_mismatch_count": 0,
                    "handoff_selected_suite_path": "builtin:standard-zh",
                }
            )
        if item.get("include_handoff_batch_review_context"):
            promotion.update(
                {
                    "handoff_selected_batch_review_status": "blocker" if item["name"] == "alpha" else "review",
                    "handoff_selected_batch_comparison_review_action_count": 2,
                    "handoff_selected_batch_comparison_blocker_action_count": 1 if item["name"] == "alpha" else 0,
                    "handoff_selected_batch_maturity_coverage_regression_count": 1,
                    "handoff_batch_comparison_review_action_count": 2,
                    "handoff_batch_comparison_blocker_action_count": 1 if item["name"] == "alpha" else 0,
                    "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"] if item["name"] == "alpha" else [],
                }
            )
        if item.get("require_clean_batch_review"):
            promotion["clean_batch_review_guard"] = {
                "handoff_require_clean_batch_review": True,
                "handoff_clean_batch_review_status": clean_batch_review_status,
            }
            promotion.setdefault("summary", {})
            promotion["summary"].update(
                {
                    "handoff_require_clean_batch_review": True,
                    "handoff_clean_batch_review_status": clean_batch_review_status,
                }
            )
        _apply_ci_regression(promotion, item)
        _apply_suite_design_regression(promotion, item)
        if item.get("force_compare_ready"):
            promotion["promoted_for_comparison"] = True
        if (
            item.get("require_clean_batch_review")
            and (
                clean_batch_review_status != "clean"
                or item.get("batch_ci_regression_count")
                or item.get("batch_suite_design_regression_count")
            )
            and not item.get("force_compare_ready")
        ):
            promoted = False
            promotion["promoted_for_comparison"] = False
        promotions.append(promotion)
        if promoted:
            compare_names.append(item["name"])
            compare_paths.append(rel_run_path)
    write_json(
        index_dir / "training_scale_promotion_index.json",
        {
            "title": "test promotion index",
            "generated_at": "2026-05-14T00:00:00Z",
            "summary": {
                "promotion_count": len(entries),
                "promoted_count": len(compare_names),
                "review_count": sum(1 for item in entries if item["status"] == "review"),
                "blocked_count": sum(1 for item in entries if item["status"] == "blocked"),
                "comparison_ready_count": len(compare_names),
                "handoff_require_clean_batch_review_count": sum(1 for item in entries if item.get("require_clean_batch_review")),
                "handoff_clean_batch_review_count": sum(
                    1
                    for item in entries
                    if item.get("require_clean_batch_review") and item.get("clean_batch_review_status") == "clean"
                ),
                "handoff_unclean_batch_review_count": sum(
                    1
                    for item in entries
                    if item.get("require_clean_batch_review") and item.get("clean_batch_review_status") != "clean"
                ),
                "compare_command_ready": len(compare_names) >= 2,
            },
            "promotions": promotions,
            "comparison_inputs": {
                "run_count": len(compare_names),
                "names": compare_names,
                "training_scale_run_paths": compare_paths,
                "baseline_name": baseline_name or (compare_names[0] if compare_names else None),
                "compare_command_ready": len(compare_names) >= 2,
            },
        },
    )
    return index_dir


def _apply_ci_regression(promotion: dict, item: dict) -> None:
    if not item.get("batch_ci_regression_count"):
        return
    fields = {
        "handoff_batch_maturity_ci_regression_count": item.get("batch_ci_regression_count"),
        "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count": item.get(
            "batch_boundary_plan_regression_count"
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": item.get("batch_ci_regression_reason_counts"),
        "handoff_batch_maturity_ci_regression_names": item.get("batch_ci_regression_names"),
        "handoff_selected_batch_maturity_ci_regression_count": item.get("selected_batch_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count": item.get(
            "selected_batch_boundary_plan_regression_count"
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": item.get("selected_batch_ci_regression_reason_counts"),
    }
    promotion.update(fields)
    promotion.setdefault("summary", {}).update(fields)
    if "clean_batch_review_guard" in promotion:
        promotion["clean_batch_review_guard"].update(fields)


def _apply_suite_design_regression(promotion: dict, item: dict) -> None:
    if not item.get("batch_suite_design_regression_count"):
        return
    fields = {
        "handoff_batch_maturity_suite_design_regression_count": item.get("batch_suite_design_regression_count"),
        "handoff_batch_maturity_suite_design_regression_names": item.get("batch_suite_design_regression_names"),
        "handoff_selected_batch_maturity_suite_design_regression_count": item.get("selected_batch_suite_design_regression_count"),
        "handoff_selected_batch_maturity_suite_design_regression_names": item.get("selected_batch_suite_design_regression_names"),
    }
    promotion.update(fields)
    promotion.setdefault("summary", {}).update(fields)
    if "clean_batch_review_guard" in promotion:
        promotion["clean_batch_review_guard"].update(fields)


def scale_run(name: str, gate_status: str, suite_name: str | None = "standard-zh") -> dict:
    suite = (
        {"suite_mode": "builtin", "suite_name": suite_name, "suite_path": f"builtin:{suite_name}"}
        if suite_name
        else {"suite_mode": "file", "suite_name": None, "suite_path": str(ROOT / "data" / "eval_prompts.json")}
    )
    return {
        "name": name,
        "status": "completed",
        "allowed": True,
        "execute": True,
        "gate_profile": "review",
        "gate": {
            "overall_status": gate_status,
            "pass_count": 2 if gate_status == "pass" else 1,
            "warn_count": 0 if gate_status == "pass" else 1,
            "fail_count": 0,
        },
        "scale_plan_summary": {
            "dataset_name": "sample-zh",
            "version_prefix": "v79-test",
            "scale_tier": "tiny",
            "char_count": 1024,
            "warning_count": 0 if gate_status == "pass" else 1,
            "variant_count": 1,
            "baseline": name,
            **suite,
        },
        "batch_summary": {
            "status": "completed",
            "comparison_status": "written",
            "variant_count": 1,
            "completed_variant_count": 1,
        },
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
