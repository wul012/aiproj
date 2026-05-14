from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed import (  # noqa: E402
    build_promoted_training_scale_seed,
    write_promoted_training_scale_seed_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the next MiniGPT training scale seed from a promoted baseline decision.")
    parser.add_argument("decision", type=Path, help="promoted_training_scale_decision.json file or decision directory")
    parser.add_argument("sources", nargs="*", type=Path, help="Next-cycle corpus text files or directories")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "promoted-training-scale-seed")
    parser.add_argument("--plan-out-dir", type=Path, default=ROOT / "runs" / "training-scale-plan-from-promoted-baseline")
    parser.add_argument("--batch-out-root", type=Path, default=ROOT / "runs" / "training-portfolio-batch-from-promoted-baseline")
    parser.add_argument("--dataset-name", type=str, default="portfolio-zh")
    parser.add_argument("--dataset-version-prefix", type=str, default="v81")
    parser.add_argument("--dataset-description", type=str, default="MiniGPT corpus seeded from a promoted training scale baseline.")
    parser.add_argument("--sample-prompt", type=str, default="MiniGPT")
    parser.add_argument("--max-variants", type=int, default=3)
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--title", type=str, default="MiniGPT promoted training scale next-cycle seed")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the next-cycle seed is ready")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_promoted_training_scale_seed(
        args.decision,
        args.sources,
        project_root=args.project_root,
        plan_out_dir=args.plan_out_dir,
        batch_out_root=args.batch_out_root,
        dataset_name=args.dataset_name,
        dataset_version_prefix=args.dataset_version_prefix,
        dataset_description=args.dataset_description,
        sample_prompt=args.sample_prompt,
        max_variants=args.max_variants,
        python_executable=args.python,
        title=args.title,
    )
    outputs = write_promoted_training_scale_seed_outputs(report, args.out_dir)
    summary = report["summary"]
    seed = report["baseline_seed"]
    plan = report["next_plan"]
    print(f"seed_status={report['seed_status']}")
    print(f"selected_baseline={seed.get('selected_name')}")
    print(f"decision_status={seed.get('decision_status')}")
    print(f"source_count={summary.get('source_count')}")
    print(f"missing_source_count={summary.get('missing_source_count')}")
    print(f"command_available={plan.get('command_available')}")
    print(f"execution_ready={plan.get('execution_ready')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print(f"next_plan_command={plan.get('command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if args.require_ready and report["seed_status"] != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
