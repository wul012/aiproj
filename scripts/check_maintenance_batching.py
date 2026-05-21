from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maintenance_policy import (
    build_governance_stabilization_review,
    build_maintenance_batching_report,
    build_module_pressure_report,
    write_governance_stabilization_outputs,
    write_maintenance_batching_outputs,
    write_module_pressure_outputs,
)


DEFAULT_RECENT_HISTORY = [
    {"version": "v101", "title": "MiniGPT v101 release readiness comparison report-utils migration", "category": "report-utils", "modules": ["release_readiness_comparison.py"]},
    {"version": "v102", "title": "MiniGPT v102 release readiness report-utils migration", "category": "report-utils", "modules": ["release_readiness.py"]},
    {"version": "v103", "title": "MiniGPT v103 training scale workflow report-utils migration", "category": "report-utils", "modules": ["training_scale_workflow.py"]},
    {"version": "v104", "title": "MiniGPT v104 release bundle report-utils migration", "category": "report-utils", "modules": ["release_bundle.py"]},
    {
        "version": "v108",
        "title": "MiniGPT v108 batched release governance report utility migration",
        "category": "report-utils",
        "modules": ["release_gate.py", "release_gate_comparison.py", "request_history_summary.py"],
    },
]

DEFAULT_PROPOSAL = [
    {"name": "registry.py report helpers", "category": "report-utils", "risk_flags": []},
    {"name": "benchmark_scorecard.py report helpers", "category": "report-utils", "risk_flags": []},
    {"name": "project_audit.py report helpers", "category": "report-utils", "risk_flags": []},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MiniGPT maintenance version batching policy.")
    parser.add_argument("--history", type=Path, default=None, help="Optional JSON list of recent version entries.")
    parser.add_argument("--proposal", type=Path, default=None, help="Optional JSON list of proposed maintenance items.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "maintenance-batching")
    parser.add_argument("--title", type=str, default="MiniGPT maintenance batching policy")
    parser.add_argument("--single-module-limit", type=int, default=3)
    parser.add_argument("--min-batch-items", type=int, default=2)
    parser.add_argument("--module-scope", type=Path, default=ROOT / "src" / "minigpt", help="Python file or directory to scan for module size pressure.")
    parser.add_argument("--module-warning-lines", type=int, default=700)
    parser.add_argument("--module-critical-lines", type=int, default=1200)
    parser.add_argument("--module-top-n", type=int, default=12)
    parser.add_argument("--skip-module-pressure", action="store_true", help="Only write the v109 batching report.")
    parser.add_argument("--governance-chains", type=Path, default=None, help="Optional JSON list of governance chains to stabilize.")
    parser.add_argument("--governance-proposals", type=Path, default=None, help="Optional JSON list of governance expansion proposals to route.")
    parser.add_argument("--governance-pause-days", type=int, default=3)
    parser.add_argument("--require-clean-governance-routing", action="store_true", help="Exit non-zero when governance proposals require review or new-chain rejection.")
    parser.add_argument("--skip-governance-stabilization", action="store_true", help="Skip governance stabilization review outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    history = _read_json_list(args.history, DEFAULT_RECENT_HISTORY)
    proposal = _read_json_list(args.proposal, DEFAULT_PROPOSAL)
    report = build_maintenance_batching_report(
        history,
        proposal_items=proposal,
        title=args.title,
        single_module_limit=args.single_module_limit,
        min_batch_items=args.min_batch_items,
    )
    outputs = write_maintenance_batching_outputs(report, args.out_dir)
    module_outputs: dict[str, str] = {}
    module_report = None
    governance_outputs: dict[str, str] = {}
    governance_report = None
    if not args.skip_module_pressure:
        module_paths = _collect_python_paths(args.module_scope)
        module_report = build_module_pressure_report(
            module_paths,
            project_root=ROOT,
            title="MiniGPT module pressure audit",
            warning_lines=args.module_warning_lines,
            critical_lines=args.module_critical_lines,
            top_n=args.module_top_n,
        )
        module_outputs = write_module_pressure_outputs(module_report, args.out_dir)
    if not args.skip_governance_stabilization:
        governance_chains = _read_json_list(args.governance_chains, []) if args.governance_chains is not None else None
        governance_proposals = _read_json_list(args.governance_proposals, []) if args.governance_proposals is not None else None
        governance_report = build_governance_stabilization_review(
            governance_chains,
            proposed_items=governance_proposals,
            pause_days=args.governance_pause_days,
        )
        governance_report["routing_requirement"] = build_governance_routing_requirement(
            governance_report["proposal_routing"],
            required=args.require_clean_governance_routing,
        )
        governance_outputs = write_governance_stabilization_outputs(governance_report, args.out_dir)
    summary = report["summary"]
    proposal_summary = report["proposal"]
    print(f"status={summary['status']}")
    print(f"decision={summary['decision']}")
    print(f"entries={summary['entry_count']}")
    print(f"single_module_utils={summary['single_module_utils_count']}")
    print(f"batched_utils={summary['batched_utils_count']}")
    print(f"longest_single_module_utils_run={summary['longest_single_module_utils_run']}")
    print(f"proposal_decision={proposal_summary['decision']}")
    print(f"proposal_target={proposal_summary['target_version_kind']}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if module_report is not None:
        module_summary = module_report["summary"]
        print(f"module_pressure_status={module_summary['status']}")
        print(f"module_pressure_decision={module_summary['decision']}")
        print(f"module_count={module_summary['module_count']}")
        print(f"module_warn_count={module_summary['warn_count']}")
        print(f"module_critical_count={module_summary['critical_count']}")
        print(f"largest_module={module_summary['largest_module']}")
        print("module_outputs=" + json.dumps(module_outputs, ensure_ascii=False))
    if governance_report is not None:
        governance_summary = governance_report["summary"]
        print(f"governance_status={governance_summary['status']}")
        print(f"governance_decision={governance_summary['decision']}")
        print(f"governance_pause_days={governance_summary['pause_days']}")
        print(f"governance_chain_count={governance_summary['chain_count']}")
        print(f"governance_keep_count={governance_summary['keep_count']}")
        print(f"governance_watch_count={governance_summary['watch_count']}")
        print(f"governance_missing_review_reason_count={governance_summary['missing_review_reason_count']}")
        print(f"governance_missing_expansion_rule_count={governance_summary['missing_expansion_rule_count']}")
        print(f"governance_consolidation_candidate_count={governance_summary['consolidation_candidate_count']}")
        governance_routing = governance_report["proposal_routing"]
        print(f"governance_routing_decision={governance_routing['decision']}")
        print(f"governance_routing_item_count={governance_routing['item_count']}")
        print(f"governance_routing_merge_existing_count={governance_routing['merge_existing_count']}")
        print(f"governance_routing_review_count={governance_routing['review_count']}")
        print(f"governance_routing_new_chain_candidate_count={governance_routing['new_chain_candidate_count']}")
        print(f"governance_routing_exact_match_count={governance_routing['exact_match_count']}")
        print(f"governance_routing_keyword_match_count={governance_routing['keyword_match_count']}")
        print(f"governance_routing_ambiguous_keyword_match_count={governance_routing['ambiguous_keyword_match_count']}")
        print("governance_routing_keyword_hits=" + ",".join(str(item) for item in governance_routing.get("keyword_hits", [])))
        print("governance_routing_ambiguous_keyword_hits=" + ",".join(str(item) for item in governance_routing.get("ambiguous_keyword_hits", [])))
        routing_gate = governance_report["routing_requirement"]
        print(f"governance_routing_requirement_status={routing_gate['status']}")
        print(f"governance_routing_requirement_decision={routing_gate['decision']}")
        print(f"governance_routing_requirement_exit_code={routing_gate['exit_code']}")
        print(f"governance_routing_requirement_blocking_count={routing_gate['blocking_count']}")
        print("governance_routing_requirement_failed_reasons=" + ",".join(str(item) for item in routing_gate.get("failed_reasons", [])))
        print("governance_outputs=" + json.dumps(governance_outputs, ensure_ascii=False))
        if routing_gate["exit_code"]:
            raise SystemExit(int(routing_gate["exit_code"]))


def _read_json_list(path: Path | None, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if path is None:
        return [dict(item) for item in fallback]
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _collect_python_paths(scope: Path) -> list[Path]:
    if scope.is_file():
        return [scope]
    if not scope.exists():
        raise FileNotFoundError(f"Module pressure scope does not exist: {scope}")
    return sorted(path for path in scope.rglob("*.py") if path.is_file())


def build_governance_routing_requirement(routing: dict[str, Any], *, required: bool = False) -> dict[str, Any]:
    review_count = int(routing.get("review_count") or 0)
    new_chain_candidate_count = int(routing.get("new_chain_candidate_count") or 0)
    ambiguous_keyword_match_count = int(routing.get("ambiguous_keyword_match_count") or 0)
    blocking_count = review_count + new_chain_candidate_count
    failed_reasons: list[str] = []
    if review_count:
        failed_reasons.append("review_required")
    if new_chain_candidate_count:
        failed_reasons.append("new_chain_candidate")
    if ambiguous_keyword_match_count:
        failed_reasons.append("ambiguous_keyword")
    if not required:
        return {
            "required": False,
            "status": "not-required",
            "decision": "report-only",
            "exit_code": 0,
            "blocking_count": blocking_count,
            "failed_reasons": failed_reasons,
        }
    status = "pass" if blocking_count == 0 else "fail"
    return {
        "required": True,
        "status": status,
        "decision": "continue" if status == "pass" else "stop",
        "exit_code": 0 if status == "pass" else 1,
        "blocking_count": blocking_count,
        "failed_reasons": failed_reasons,
    }


if __name__ == "__main__":
    main()
