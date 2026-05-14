from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_promotion import (  # noqa: E402
    build_training_scale_promotion,
    write_training_scale_promotion_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote or block a completed MiniGPT training scale handoff.")
    parser.add_argument("handoff", type=Path, help="training_scale_handoff.json file or handoff output directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults beside the handoff report")
    parser.add_argument("--title", type=str, default="MiniGPT training scale promotion")
    parser.add_argument("--no-fail", action="store_true", help="Write the report even when promotion is blocked and exit zero")
    return parser.parse_args()


def default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "promotion"
    if path.name == "training_scale_handoff.json":
        return path.parent / "promotion"
    return path.parent / "training-scale-promotion"


def main() -> None:
    args = parse_args()
    report = build_training_scale_promotion(args.handoff, title=args.title)
    outputs = write_training_scale_promotion_outputs(report, args.out_dir or default_out_dir(args.handoff))
    summary = report["summary"]
    print(f"promotion_status={summary['promotion_status']}")
    print(f"handoff_status={summary.get('handoff_status')}")
    print(f"scale_run_status={summary.get('scale_run_status')}")
    print(f"batch_status={summary.get('batch_status')}")
    print(f"ready_variants={summary.get('ready_variant_count')}/{summary.get('variant_count')}")
    print(f"required_artifacts={summary.get('available_required_artifact_count')}/{summary.get('required_artifact_count')}")
    print("summary=" + json.dumps(summary, ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if summary["promotion_status"] == "blocked" and not args.no_fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
