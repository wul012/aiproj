from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.baseline_candidate_handoff_check import (  # noqa: E402
    build_baseline_candidate_handoff_check,
    render_baseline_candidate_handoff_check_text,
    write_baseline_candidate_handoff_check_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a MiniGPT baseline-candidate handoff contract.")
    parser.add_argument("handoff", type=Path, help="Path to baseline_candidate_handoff.json or its directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "baseline-candidate-handoff-check")
    parser.add_argument("--require-pass", action="store_true", help="Exit with 1 when the handoff check fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_baseline_candidate_handoff_check(args.handoff)
    outputs = write_baseline_candidate_handoff_check_outputs(report, args.out_dir)
    print(render_baseline_candidate_handoff_check_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    exit_code = resolve_exit_code(report, require_pass=args.require_pass)
    if exit_code:
        raise SystemExit(exit_code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    main()
