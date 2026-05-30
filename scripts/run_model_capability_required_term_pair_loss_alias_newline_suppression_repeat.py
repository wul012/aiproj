from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_repeat import (  # noqa: E402
    build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_repeat_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text,
    write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repeat newline suppression probes across loss-alias focus reports.")
    parser.add_argument("focus", nargs="+", type=Path, help="Focus report JSON files or output directories.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "model-capability-required-term-pair-loss-alias-newline-suppression-repeat",
    )
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the repeat report fails structurally.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat(
        args.focus,
        out_dir=args.out_dir,
    )
    outputs = write_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_loss_alias_newline_suppression_repeat_text(report), end="")
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
