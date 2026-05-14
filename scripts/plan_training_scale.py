from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_plan import (  # noqa: E402
    build_training_scale_plan,
    write_training_scale_plan_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan scale-aware MiniGPT training variants for a text corpus.")
    parser.add_argument("sources", nargs="+", type=Path, help="Training text files or directories")
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "training-scale-plan")
    parser.add_argument("--batch-out-root", type=Path, default=None)
    parser.add_argument("--dataset-name", type=str, default="portfolio-zh")
    parser.add_argument("--dataset-version-prefix", type=str, default="v70")
    parser.add_argument("--dataset-description", type=str, default="MiniGPT corpus planned for scale-aware training.")
    parser.add_argument("--max-variants", type=int, default=3)
    parser.add_argument("--sample-prompt", type=str, default="MiniGPT")
    parser.add_argument("--python", type=str, default=sys.executable)
    parser.add_argument("--title", type=str, default="MiniGPT training scale plan")
    parser.add_argument("--no-recursive", action="store_true", help="Only read top-level .txt files from directories.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_training_scale_plan(
        args.sources,
        project_root=args.project_root,
        out_root=args.out_dir,
        batch_out_root=args.batch_out_root,
        dataset_name=args.dataset_name,
        dataset_version_prefix=args.dataset_version_prefix,
        dataset_description=args.dataset_description,
        recursive=not args.no_recursive,
        max_variants=args.max_variants,
        python_executable=args.python,
        sample_prompt=args.sample_prompt,
        title=args.title,
    )
    outputs = write_training_scale_plan_outputs(report, args.out_dir)
    dataset = report["dataset"]
    batch = report["batch"]
    print(f"scale_tier={dataset.get('scale_tier')}")
    print(f"source_count={dataset.get('source_count')}")
    print(f"char_count={dataset.get('char_count')}")
    print(f"quality_status={dataset.get('quality_status')}")
    print(f"warning_count={dataset.get('warning_count')}")
    print(f"variant_count={len(report.get('variants', []))}")
    print(f"baseline={batch.get('baseline')}")
    print("batch_command=" + json.dumps(batch.get("command"), ensure_ascii=False))
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    main()
