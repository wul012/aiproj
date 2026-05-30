from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_decoding_sweep import (  # noqa: E402
    build_model_capability_required_term_pair_decoding_sweep,
    default_pair_decoding_profiles,
    locate_model_capability_required_term_pair_decoding_sweep_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_decoding_sweep_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_decoding_sweep_text,
    write_model_capability_required_term_pair_decoding_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep decoding profiles for partial v497 pair-capacity checkpoints.")
    parser.add_argument("pair_capacity_sweep", type=Path, help="Path to v497 pair-capacity JSON or directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-decoding-sweep",
    )
    parser.add_argument("--seed", type=int, default=498, help="Base generation seed for decoding profiles.")
    parser.add_argument("--target-limit", type=int, default=2)
    parser.add_argument(
        "--profile-preset",
        choices=("default", "fast"),
        default="default",
        help="default runs 4 decoding profiles; fast keeps only deterministic-12.",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_pair_decoding_sweep_source(args.pair_capacity_sweep)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_decoding_sweep(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        seed=args.seed,
        target_limit=args.target_limit,
        decoding_profiles=decoding_profiles(args.profile_preset),
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_decoding_sweep_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_decoding_sweep_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def decoding_profiles(preset: str) -> list[dict[str, object]]:
    profiles = default_pair_decoding_profiles()
    if preset == "fast":
        return profiles[:1]
    return profiles


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
