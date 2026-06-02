from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic import (  # noqa: E402
    build_prompt_surface_sensitivity_diagnostic,
    locate_prompt_surface_sensitivity_replay_source,
    locate_prompt_surface_sensitivity_training_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic_artifacts import (  # noqa: E402
    render_prompt_surface_sensitivity_diagnostic_text,
    write_prompt_surface_sensitivity_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose prompt-surface sensitivity between a training run and independent pair-probe replay.")
    parser.add_argument("training_run", type=Path, help="Training run JSON or output directory.")
    parser.add_argument("pair_probe_replay", type=Path, help="Pair-probe replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-fixed-preserving-transfer-prompt-surface-sensitivity-diagnostic")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when diagnostic execution fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    training_source = locate_prompt_surface_sensitivity_training_source(args.training_run)
    replay_source = locate_prompt_surface_sensitivity_replay_source(args.pair_probe_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_prompt_surface_sensitivity_diagnostic(
        read_json_report(training_source),
        read_json_report(replay_source),
        training_source_path=training_source,
        replay_source_path=replay_source,
    )
    outputs = write_prompt_surface_sensitivity_diagnostic_outputs(report, args.out_dir)
    print(render_prompt_surface_sensitivity_diagnostic_text(report), end="")
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
