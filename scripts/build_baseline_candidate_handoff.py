from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_handoff import (  # noqa: E402
    build_baseline_candidate_handoff,
    render_baseline_candidate_handoff_text,
    write_baseline_candidate_handoff_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a MiniGPT baseline-candidate handoff from a loop report.")
    parser.add_argument("loop_report", type=Path, help="Path to baseline_candidate_eval_loop.json or its directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-handoff")
    parser.add_argument("--require-accepted", action="store_true", help="Exit with 2 when the candidate is not ready for handoff.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    handoff = build_baseline_candidate_handoff(args.loop_report)
    outputs = write_baseline_candidate_handoff_outputs(handoff, args.out_dir)
    print(render_baseline_candidate_handoff_text(handoff), end="")
    for key, path in outputs.items():
        print(f"saved_{key}={path}")
    exit_code = resolve_exit_code(handoff, require_accepted=args.require_accepted)
    if exit_code:
        raise SystemExit(exit_code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(handoff: dict[str, Any], *, require_accepted: bool) -> int:
    if handoff.get("status") != "pass":
        return 1
    if require_accepted and not handoff.get("handoff_ready"):
        return 2
    return 0


if __name__ == "__main__":
    main()
