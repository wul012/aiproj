from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge import (  # noqa: E402
    build_bounded_objective_loss_signal_bridge,
    locate_profile_sweep,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_artifacts import (  # noqa: E402
    render_loss_signal_bridge_text,
    write_loss_signal_bridge_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a no-anchor bridge corpus from bounded-objective loss signal profile rows.")
    parser.add_argument("--profile-sweep", type=Path, required=True)
    parser.add_argument("--source-corpus", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge")
    parser.add_argument("--require-bridge-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    sweep_path = locate_profile_sweep(args.profile_sweep)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_bounded_objective_loss_signal_bridge(
        read_json_report(sweep_path),
        source_corpus_path=args.source_corpus,
        profile_sweep_path=sweep_path,
    )
    outputs = write_loss_signal_bridge_outputs(report, args.out_dir)
    print(render_loss_signal_bridge_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_bridge_ready=args.require_bridge_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
