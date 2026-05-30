from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_decoding_gap_probe import (  # noqa: E402
    build_model_capability_required_term_pair_decoding_gap_probe,
    locate_model_capability_required_term_pair_decoding_gap_probe_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_decoding_gap_probe_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_decoding_gap_probe_text,
    write_model_capability_required_term_pair_decoding_gap_probe_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe generation-side expression for forced-choice gap variants.")
    parser.add_argument("generation_gap_report", type=Path, help="Path to v504 generation-gap JSON or directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-decoding-gap-probe",
    )
    parser.add_argument("--forced-choice-report", type=Path, default=None)
    parser.add_argument("--variant-limit", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_pair_decoding_gap_probe_source(args.generation_gap_report)
    prepare_output_dir(args.out_dir, force=args.force)
    forced_report = read_json_report(args.forced_choice_report) if args.forced_choice_report else None
    report = build_model_capability_required_term_pair_decoding_gap_probe(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        forced_choice_report=forced_report,
        forced_choice_path=args.forced_choice_report,
        variant_limit=args.variant_limit,
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_decoding_gap_probe_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_decoding_gap_probe_text(report), end="")
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
