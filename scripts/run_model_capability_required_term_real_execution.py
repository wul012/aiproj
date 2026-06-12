from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_real_execution import (  # noqa: E402
    build_required_term_real_execution,
    create_required_term_tiny_checkpoint,
    read_json_report,
    resolve_exit_code,
    write_required_term_real_execution_outputs,
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v1143 real required-term coverage execution for capability-regression-01.")
    parser.add_argument("--suite-manifest", type=Path, default=DEFAULT_MANIFEST, help="v1137 suite manifest JSON.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output" / "model-capability-required-term-real-execution-v1143")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Existing MiniGPT checkpoint. If omitted, a deterministic tiny checkpoint is created under out-dir.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Existing tokenizer JSON. Required when --checkpoint is passed.")
    parser.add_argument("--device", choices=["cpu", "auto", "cuda"], default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 if the real required-term execution does not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    paths = _resolve_model_paths(args)
    manifest = read_json_report(args.suite_manifest)
    report = build_required_term_real_execution(
        manifest,
        checkpoint_path=paths["checkpoint"],
        tokenizer_path=paths["tokenizer"],
        device=args.device,
        suite_manifest_path=args.suite_manifest,
    )
    outputs = write_required_term_real_execution_outputs(report, args.out_dir)
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
        return create_required_term_tiny_checkpoint(args.out_dir / "tiny-required-term-checkpoint")
    if args.tokenizer is None:
        raise SystemExit("--tokenizer is required when --checkpoint is provided")
    return {"checkpoint": str(args.checkpoint), "tokenizer": str(args.tokenizer)}


if __name__ == "__main__":
    main()
