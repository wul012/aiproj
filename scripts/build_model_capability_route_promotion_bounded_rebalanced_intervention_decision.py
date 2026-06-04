from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_rebalanced_intervention_decision,
    locate_rebalanced_comparison,
    locate_rebalanced_failure_diagnostic,
    locate_rebalanced_profile_sweep,
    locate_rebalanced_seed_revision,
    locate_rebalanced_training_run,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision_artifacts import (  # noqa: E402
    render_bounded_rebalanced_intervention_decision_text,
    write_bounded_rebalanced_intervention_decision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Decide whether to stop the bounded rebalanced decoder-rescue route and plan the next intervention.")
    parser.add_argument("--rebalanced-seed", type=Path, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--failure-diagnostic", type=Path, required=True)
    parser.add_argument("--profile-sweep", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-rebalanced-intervention-decision")
    parser.add_argument("--require-decision-ready", action="store_true")
    parser.add_argument("--require-intervention-selected", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_rebalanced_seed_revision(args.rebalanced_seed)
    training_path = locate_rebalanced_training_run(args.training_run)
    comparison_path = locate_rebalanced_comparison(args.comparison)
    diagnostic_path = locate_rebalanced_failure_diagnostic(args.failure_diagnostic)
    sweep_path = locate_rebalanced_profile_sweep(args.profile_sweep)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
        read_json_report(seed_path),
        read_json_report(training_path),
        read_json_report(comparison_path),
        read_json_report(diagnostic_path),
        read_json_report(sweep_path),
        seed_revision_path=seed_path,
        training_run_path=training_path,
        comparison_path=comparison_path,
        failure_diagnostic_path=diagnostic_path,
        profile_sweep_path=sweep_path,
    )
    outputs = write_bounded_rebalanced_intervention_decision_outputs(report, args.out_dir)
    print(render_bounded_rebalanced_intervention_decision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_decision_ready=args.require_decision_ready,
        require_intervention_selected=args.require_intervention_selected,
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
