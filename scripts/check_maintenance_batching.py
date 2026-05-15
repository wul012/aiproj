from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maintenance_policy import build_maintenance_batching_report, write_maintenance_batching_outputs


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


def _read_json_list(path: Path | None, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if path is None:
        return [dict(item) for item in fallback]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list")
    return [dict(item) for item in payload if isinstance(item, dict)]


if __name__ == "__main__":
    main()
