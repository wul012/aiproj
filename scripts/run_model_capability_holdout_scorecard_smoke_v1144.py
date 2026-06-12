from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_holdout_scorecard_smoke import (  # noqa: E402
    build_holdout_scorecard_smoke,
    create_holdout_scorecard_tiny_checkpoint,
    read_json_report,
    resolve_exit_code,
    write_holdout_scorecard_smoke_outputs,
)
from minigpt.readability_report_artifacts import render_readability_text  # noqa: E402

DEFAULT_MANIFEST = (
    ROOT
    / "f"
    / "1137"
    / "解释"
    / "model-capability-regression-suite-manifest-v1137"
    / "model_capability_regression_suite_manifest_v1137.json"
)
DEFAULT_REQUIRED_TERM_REPORT = (
    ROOT
    / "f"
    / "1143"
    / "解释"
    / "model-capability-required-term-real-execution-v1143"
    / "model_capability_required_term_real_execution_v1143.json"
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1144 real holdout scorecard smoke for capability-regression-04.")
    parser.add_argument("--suite-manifest", type=Path, default=DEFAULT_MANIFEST, help="v1137 suite manifest JSON.")
    parser.add_argument("--required-term-real-execution", type=Path, default=DEFAULT_REQUIRED_TERM_REPORT, help="v1143 real required-term execution JSON.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "model-capability-holdout-scorecard-smoke-v1144")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Existing MiniGPT checkpoint. If omitted, a deterministic tiny checkpoint is created under out-dir.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Existing tokenizer JSON. Required when --checkpoint is passed.")
    parser.add_argument("--device", choices=["cpu", "auto", "cuda"], default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 if the smoke report does not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    paths = _resolve_model_paths(args)
    report = build_holdout_scorecard_smoke(
        read_json_report(args.suite_manifest, description="model capability regression suite manifest"),
        read_json_report(args.required_term_real_execution, description="required term real execution"),
        checkpoint_path=paths["checkpoint"],
        tokenizer_path=paths["tokenizer"],
        work_dir=args.out_dir / "real-holdout-scorecard-run",
        device=args.device,
        suite_manifest_path=args.suite_manifest,
        required_term_path=args.required_term_real_execution,
    )
    outputs = write_holdout_scorecard_smoke_outputs(report, args.out_dir)
    print(render_readability_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _resolve_model_paths(args: argparse.Namespace) -> dict[str, str]:
    if args.checkpoint is None:
        return create_holdout_scorecard_tiny_checkpoint(args.out_dir / "tiny-holdout-scorecard-checkpoint")
    if args.tokenizer is None:
        raise SystemExit("--tokenizer is required when --checkpoint is provided")
    return {"checkpoint": str(args.checkpoint), "tokenizer": str(args.tokenizer)}


if __name__ == "__main__":
    main()
