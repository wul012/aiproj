from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit import (  # noqa: E402
    build_decoder_budget_audit,
    locate_loss_token_probability_probe,
    locate_stagnation_aware_suffix_replay_comparison,
    read_json_report,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_artifacts import (  # noqa: E402
    render_decoder_budget_audit_text,
    write_decoder_budget_audit_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit whether bounded replay exhausted max-new-token budget before the top-1 loss suffix.")
    parser.add_argument("--replay-comparison", type=Path, required=True)
    parser.add_argument("--loss-token-probability-probe", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "runs" / "bounded-objective-loss-signal-bridge-target-only-memory-decoder-budget-audit",
    )
    parser.add_argument("--require-audit-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_stagnation_aware_suffix_replay_comparison(args.replay_comparison)
    probe_path = locate_loss_token_probability_probe(args.loss_token_probability_probe)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_decoder_budget_audit(
        read_json_report(replay_path),
        read_json_report(probe_path),
        tokenizer_path=args.tokenizer,
        replay_comparison_path=replay_path,
        probability_probe_path=probe_path,
    )
    outputs = write_decoder_budget_audit_outputs(report, args.out_dir)
    print(render_decoder_budget_audit_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_audit_ready=args.require_audit_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
