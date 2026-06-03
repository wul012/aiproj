from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run import (  # noqa: E402
    build_model_capability_route_promotion_bounded_benchmark_dry_run,
    locate_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_bounded_benchmark_suite_review,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_benchmark_dry_run_text,
    write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a dry-run scorer for a bounded route-promotion benchmark suite.")
    parser.add_argument("--benchmark-suite", type=Path, required=True, help="Bounded benchmark suite JSON or output directory.")
    parser.add_argument("--suite-review", type=Path, required=True, help="Bounded benchmark suite review JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-benchmark-dry-run")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the dry run fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    suite_path = locate_route_promotion_bounded_benchmark_suite(args.benchmark_suite)
    review_path = locate_route_promotion_bounded_benchmark_suite_review(args.suite_review)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_benchmark_dry_run(
        read_json_report(review_path),
        read_json_report(suite_path),
        suite_review_path=review_path,
        benchmark_suite_path=suite_path,
    )
    outputs = write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_benchmark_dry_run_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
