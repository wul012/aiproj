from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_contrast_free_route_decision import (  # noqa: E402
    build_model_capability_required_term_pair_contrast_free_route_decision,
    locate_contrast_free_comparison,
    locate_first_token_diagnostic,
    locate_prior_closeout,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_contrast_free_route_decision_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_contrast_free_route_decision_text,
    write_model_capability_required_term_pair_contrast_free_route_decision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide next step after contrast-free fixed/loss routes.")
    parser.add_argument("--comparison", type=Path, required=True, help="Contrast-free comparison JSON or output directory.")
    parser.add_argument("--prior-closeout", type=Path, required=True, help="v608 closeout JSON or output directory.")
    parser.add_argument("--first-token-diagnostic", type=Path, required=True, help="v609 diagnostic JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-contrast-free-route-decision")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when decision input is not pass.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    comparison_path = locate_contrast_free_comparison(args.comparison)
    prior_closeout_path = locate_prior_closeout(args.prior_closeout)
    first_token_path = locate_first_token_diagnostic(args.first_token_diagnostic)
    report = build_model_capability_required_term_pair_contrast_free_route_decision(
        comparison=read_json_report(comparison_path),
        prior_closeout=read_json_report(prior_closeout_path),
        first_token_diagnostic=read_json_report(first_token_path),
        comparison_path=comparison_path,
        prior_closeout_path=prior_closeout_path,
        first_token_diagnostic_path=first_token_path,
    )
    outputs = write_model_capability_required_term_pair_contrast_free_route_decision_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_contrast_free_route_decision_text(report), end="")
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
