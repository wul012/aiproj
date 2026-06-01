from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_failure_diagnostic import (  # noqa: E402
    build_model_capability_required_term_pair_surface_failure_diagnostic,
    locate_surface_failure_forced_choice_source,
    locate_surface_failure_stability_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_failure_diagnostic_artifacts import (  # noqa: E402
    render_surface_failure_diagnostic_text,
    write_surface_failure_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose internal-stable/free-generation required-term pair surface failures.")
    parser.add_argument("stability", type=Path, help="Aligned-candidate seed stability JSON or directory.")
    parser.add_argument("forced_choice", type=Path, help="Refresh forced-choice JSON or directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-failure-diagnostic")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when diagnostic inputs fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    stability_source = locate_surface_failure_stability_source(args.stability)
    forced_choice_source = locate_surface_failure_forced_choice_source(args.forced_choice)
    report = build_model_capability_required_term_pair_surface_failure_diagnostic(
        read_json_report(stability_source),
        read_json_report(forced_choice_source),
        stability_source_path=stability_source,
        forced_choice_source_path=forced_choice_source,
    )
    outputs = write_surface_failure_diagnostic_outputs(report, args.out_dir)
    print(render_surface_failure_diagnostic_text(report), end="")
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
