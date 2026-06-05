from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe import (  # noqa: E402
    build_loss_token_probability_probe,
    locate_objective_contract,
    locate_replay_delta_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_artifacts import (  # noqa: E402
    render_loss_token_probability_probe_text,
    write_loss_token_probability_probe_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe target-token probabilities after fixed-l for the bounded objective loss suffix.")
    parser.add_argument("--objective-contract", type=Path, required=True)
    parser.add_argument("--replay-delta-diagnostic", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-loss-token-probability-probe",
    )
    parser.add_argument("--require-probe-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    contract_path = locate_objective_contract(args.objective_contract)
    replay_delta_path = locate_replay_delta_diagnostic(args.replay_delta_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_loss_token_probability_probe(
        read_json_report(contract_path),
        read_json_report(replay_delta_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        top_k=args.top_k,
        objective_contract_path=contract_path,
        replay_delta_diagnostic_path=replay_delta_path,
    )
    outputs = write_loss_token_probability_probe_outputs(report, args.out_dir)
    print(render_loss_token_probability_probe_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_probe_ready=args.require_probe_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
