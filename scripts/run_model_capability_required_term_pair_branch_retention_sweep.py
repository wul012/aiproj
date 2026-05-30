from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_branch_retention_sweep import (  # noqa: E402
    build_model_capability_required_term_pair_branch_retention_sweep,
    default_pair_branch_retention_sweep_variants,
    locate_model_capability_required_term_pair_branch_retention_sweep_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_branch_retention_sweep_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_branch_retention_sweep_text,
    write_model_capability_required_term_pair_branch_retention_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train balanced variants that try to retain both pair branches.")
    parser.add_argument("loss_branch_sweep", type=Path, help="Path to v501 loss-branch sweep JSON or directory.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-branch-retention-sweep",
    )
    parser.add_argument("--seed", type=int, default=502)
    parser.add_argument("--pair-limit", type=int, default=1)
    parser.add_argument("--variant-preset", choices=("default", "fast"), default="default")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_pair_branch_retention_sweep_source(args.loss_branch_sweep)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_branch_retention_sweep(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        seed=args.seed,
        pair_limit=args.pair_limit,
        variants=branch_retention_variants(args.variant_preset),
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_branch_retention_sweep_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_branch_retention_sweep_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def branch_retention_variants(preset: str) -> list[dict[str, object]]:
    variants = default_pair_branch_retention_sweep_variants()
    if preset == "fast":
        return [
            {
                **variants[0],
                "repeat": 4,
                "isolated_repeat": 1,
                "max_iters": 12,
                "n_embd": 16,
            }
        ]
    return variants


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
