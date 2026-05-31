from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_coexistence_refresh import (  # noqa: E402
    PAIR_COEXISTENCE_REFRESH_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic import (  # noqa: E402
    PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_colon_immediate_stability import (  # noqa: E402
    PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_readiness import (  # noqa: E402
    PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_loss_branch_batch_closeout import (  # noqa: E402
    PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_CONTRACT_JSON_FILENAME,
    build_model_capability_required_term_pair_loss_branch_batch_closeout,
    locate_loss_branch_batch_report,
    read_loss_branch_batch_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_branch_batch_closeout_artifacts import (  # noqa: E402
    render_loss_branch_batch_closeout_text,
    write_loss_branch_batch_closeout_outputs,
)
from minigpt.model_capability_required_term_pair_loss_branch_objective_comparison import (  # noqa: E402
    PAIR_LOSS_BRANCH_OBJECTIVE_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_loss_branch_route_decision import (  # noqa: E402
    PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close the v589-v598 loss-branch objective batch.")
    parser.add_argument("--corpus-contract", type=Path, required=True)
    parser.add_argument("--targeted-seed", type=Path, required=True)
    parser.add_argument("--dual-anchor-seed", type=Path, required=True)
    parser.add_argument("--micro-span-seed", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--route-decision", type=Path, required=True)
    parser.add_argument("--stability", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-loss-branch-batch-closeout")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    sources = _sources(args)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_loss_branch_batch_closeout(
        corpus_contract=read_loss_branch_batch_report(sources["corpus_contract"]),
        targeted_seed=read_loss_branch_batch_report(sources["targeted_seed"]),
        dual_anchor_seed=read_loss_branch_batch_report(sources["dual_anchor_seed"]),
        micro_span_seed=read_loss_branch_batch_report(sources["micro_span_seed"]),
        comparison=read_loss_branch_batch_report(sources["comparison"]),
        route_decision=read_loss_branch_batch_report(sources["route_decision"]),
        stability=read_loss_branch_batch_report(sources["stability"]),
        diagnostic=read_loss_branch_batch_report(sources["diagnostic"]),
        readiness=read_loss_branch_batch_report(sources["readiness"]),
        paths=sources,
    )
    outputs = write_loss_branch_batch_closeout_outputs(report, args.out_dir)
    print(render_loss_branch_batch_closeout_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def _sources(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "corpus_contract": locate_loss_branch_batch_report(
            args.corpus_contract, PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_CONTRACT_JSON_FILENAME
        ),
        "targeted_seed": locate_loss_branch_batch_report(args.targeted_seed, PAIR_COEXISTENCE_REFRESH_JSON_FILENAME),
        "dual_anchor_seed": locate_loss_branch_batch_report(args.dual_anchor_seed, PAIR_COEXISTENCE_REFRESH_JSON_FILENAME),
        "micro_span_seed": locate_loss_branch_batch_report(args.micro_span_seed, PAIR_COEXISTENCE_REFRESH_JSON_FILENAME),
        "comparison": locate_loss_branch_batch_report(args.comparison, PAIR_LOSS_BRANCH_OBJECTIVE_COMPARISON_JSON_FILENAME),
        "route_decision": locate_loss_branch_batch_report(args.route_decision, PAIR_LOSS_BRANCH_ROUTE_DECISION_JSON_FILENAME),
        "stability": locate_loss_branch_batch_report(args.stability, PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME),
        "diagnostic": locate_loss_branch_batch_report(args.diagnostic, PAIR_COLON_IMMEDIATE_MISSED_SEED_DIAGNOSTIC_JSON_FILENAME),
        "readiness": locate_loss_branch_batch_report(args.readiness, PAIR_FIXED_RETENTION_OBJECTIVE_READINESS_JSON_FILENAME),
    }


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
