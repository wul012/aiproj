from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff,
    write_promoted_training_scale_seed_handoff_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or execute a MiniGPT promoted training scale seed plan command.")
    parser.add_argument("seed", type=Path, help="promoted_training_scale_seed.json file or seed directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <seed>/handoff")
    parser.add_argument("--execute", action="store_true", help="Run the generated next-cycle plan command. Default only validates it.")
    parser.add_argument("--no-allow-review", action="store_true", help="Block review-status seeds instead of allowing their plan command.")
    parser.add_argument(
        "--require-clean-evidence",
        action="store_true",
        help="Exit non-zero unless the seed handoff clean-evidence readiness is true.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale seed handoff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seed_path = Path(args.seed)
    out_dir = args.out_dir or _default_out_dir(seed_path)
    report = build_promoted_training_scale_seed_handoff(
        seed_path,
        execute=args.execute,
        allow_review=not args.no_allow_review,
        require_clean_evidence=args.require_clean_evidence,
        timeout_seconds=args.timeout_seconds,
        title=args.title,
    )
    summary = report["summary"]
    clean_evidence_requirement = report["clean_evidence_requirement"]
    outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
    execution = report["execution"]
    print(f"handoff_status={summary.get('handoff_status')}")
    print(f"seed_status={report.get('seed_status')}")
    print(f"decision_status={summary.get('decision_status')}")
    print(f"execute={report.get('execute')}")
    print(f"returncode={execution.get('returncode')}")
    print(f"available_artifacts={summary.get('available_artifact_count')}/{summary.get('artifact_count')}")
    print(f"plan_status={summary.get('plan_status')}")
    print(f"seed_suite_path={summary.get('seed_suite_path')}")
    print(f"selected_handoff_suite_consistency={summary.get('selected_handoff_suite_consistency')}")
    print(f"selected_handoff_suite_mismatch_count={summary.get('selected_handoff_suite_mismatch_count')}")
    print(f"selected_handoff_selected_batch_review_status={summary.get('selected_handoff_selected_batch_review_status')}")
    print(
        "selected_handoff_selected_batch_comparison_review_action_count="
        f"{summary.get('selected_handoff_selected_batch_comparison_review_action_count')}"
    )
    print(
        "selected_handoff_selected_batch_comparison_blocker_action_count="
        f"{summary.get('selected_handoff_selected_batch_comparison_blocker_action_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_review_count="
        f"{summary.get('comparison_ready_handoff_selected_batch_review_count')}"
    )
    print(
        "comparison_ready_handoff_selected_batch_blocker_count="
        f"{summary.get('comparison_ready_handoff_selected_batch_blocker_count')}"
    )
    print(
        "comparison_ready_handoff_batch_comparison_blocker_reasons="
        + json.dumps(summary.get("comparison_ready_handoff_batch_comparison_blocker_reasons"), ensure_ascii=False)
    )
    print(f"handoff_suite_mismatch_total={summary.get('handoff_suite_mismatch_total')}")
    print(f"plan_suite_path={summary.get('plan_suite_path')}")
    print(f"seed_handoff_suite_alignment_status={summary.get('seed_handoff_suite_alignment_status')}")
    print(f"seed_handoff_suite_alignment_mismatch_count={summary.get('seed_handoff_suite_alignment_mismatch_count')}")
    print(f"seed_handoff_clean_evidence_status={summary.get('seed_handoff_clean_evidence_status')}")
    print(f"seed_handoff_clean_evidence_ready={summary.get('seed_handoff_clean_evidence_ready')}")
    print(f"seed_handoff_clean_evidence_status_domain={summary.get('seed_handoff_clean_evidence_status_domain')}")
    print(f"next_batch_command_available={summary.get('next_batch_command_available')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print(f"command={report.get('command_text')}")
    print(f"next_batch_command={report.get('next_batch_command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_clean_evidence:
        print(f"clean_evidence_required_status={clean_evidence_requirement.get('readiness_status')}")
        print(f"clean_evidence_required_ready={clean_evidence_requirement.get('ready')}")
        print(f"clean_evidence_required_detail={clean_evidence_requirement.get('detail')}")
        print(f"clean_evidence_required={clean_evidence_requirement.get('status')}")
        if clean_evidence_requirement.get("status") == "fail":
            raise SystemExit(1)
    if summary.get("handoff_status") in {"blocked", "failed", "timeout"}:
        raise SystemExit(1)


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "handoff"
    return path.parent / "handoff"


if __name__ == "__main__":
    main()
