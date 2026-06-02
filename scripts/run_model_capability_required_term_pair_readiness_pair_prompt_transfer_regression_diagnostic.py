from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic import (  # noqa: E402
    build_pair_prompt_transfer_regression_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic_artifacts import (  # noqa: E402
    render_pair_prompt_transfer_regression_diagnostic_text,
    write_pair_prompt_transfer_regression_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose pair prompt transfer regression against direct-completion evidence.")
    parser.add_argument("--direct-completion-training", type=Path, required=True, help="v738 direct-completion training report JSON.")
    parser.add_argument("--pair-probe-replay", type=Path, required=True, help="v740 pair-probe replay report JSON.")
    parser.add_argument("--transfer-training", type=Path, required=True, help="v744 pair prompt transfer training report JSON.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "pair-prompt-transfer-regression-diagnostic")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when diagnostic inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_pair_prompt_transfer_regression_diagnostic(
        direct_completion_training_report=read_json_report(args.direct_completion_training),
        pair_probe_replay_report=read_json_report(args.pair_probe_replay),
        transfer_training_report=read_json_report(args.transfer_training),
        direct_completion_path=args.direct_completion_training,
        pair_probe_path=args.pair_probe_replay,
        transfer_path=args.transfer_training,
    )
    outputs = write_pair_prompt_transfer_regression_diagnostic_outputs(report, args.out_dir)
    print(render_pair_prompt_transfer_regression_diagnostic_text(report), end="")
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
