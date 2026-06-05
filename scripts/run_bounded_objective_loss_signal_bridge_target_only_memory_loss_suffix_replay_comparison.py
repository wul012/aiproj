from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison import (  # noqa: E402
    build_loss_suffix_replay_comparison,
    locate_loss_suffix_training_run,
    locate_objective_contract,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison_artifacts import (  # noqa: E402
    render_loss_suffix_replay_comparison_text,
    write_loss_suffix_replay_comparison_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay the bounded objective contract against a loss-suffix checkpoint.")
    parser.add_argument("--objective-contract", type=Path, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-comparison")
    parser.add_argument("--require-comparison-ready", action="store_true")
    parser.add_argument("--require-objective-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    contract_path = locate_objective_contract(args.objective_contract)
    training_path = locate_loss_suffix_training_run(args.training_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_loss_suffix_replay_comparison(
        read_json_report(contract_path),
        read_json_report(training_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        objective_contract_path=contract_path,
        loss_suffix_training_run_path=training_path,
    )
    outputs = write_loss_suffix_replay_comparison_outputs(report, args.out_dir)
    print(render_loss_suffix_replay_comparison_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_comparison_ready=args.require_comparison_ready,
        require_objective_pass=args.require_objective_pass,
    )
    if code:
        raise SystemExit(code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
