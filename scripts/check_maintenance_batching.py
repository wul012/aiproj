from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maintenance_policy import (
    build_maintenance_batching_report,
    build_module_pressure_report,
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


def _read_json_list(path: Path | None, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if path is None:
        return [dict(item) for item in fallback]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list")
    return [dict(item) for item in payload if isinstance(item, dict)]


def _collect_python_paths(scope: Path) -> list[Path]:
    if scope.is_file():
        return [scope]
    if not scope.exists():
        raise FileNotFoundError(f"Module pressure scope does not exist: {scope}")
    return sorted(path for path in scope.rglob("*.py") if path.is_file())


if __name__ == "__main__":
    main()
