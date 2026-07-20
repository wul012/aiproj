from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_contrast_free_batch_closeout import (  # noqa: E402
    CONTRAST_FREE_CORPUS_CONTRACT_JSON_FILENAME,
    build_model_capability_required_term_pair_contrast_free_batch_closeout,
    locate_batch_report,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_contrast_free_batch_closeout_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_contrast_free_batch_closeout_text,
    write_model_capability_required_term_pair_contrast_free_batch_closeout_outputs,
)
from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME  # noqa: E402
from minigpt.model_capability_required_term_pair_contrast_free_route_decision import (  # noqa: E402
    PAIR_CONTRAST_FREE_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import (  # noqa: E402
    PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (  # noqa: E402
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close out the contrast-free required-term pair batch.")
    parser.add_argument("--corpus-contract", type=Path, required=True)
    parser.add_argument("--refresh-report", type=Path, action="append", required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--route-decision", type=Path, required=True)
    parser.add_argument("--forced-choice", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-contrast-free-batch-closeout")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    corpus_path = locate_batch_report(args.corpus_contract, CONTRAST_FREE_CORPUS_CONTRACT_JSON_FILENAME)
    refresh_paths = [locate_batch_report(path, PAIR_COEXISTENCE_REFRESH_JSON_FILENAME) for path in args.refresh_report]
    comparison_path = locate_batch_report(args.comparison, PAIR_FIXED_RETENTION_OBJECTIVE_COMPARISON_JSON_FILENAME)
    route_path = locate_batch_report(args.route_decision, PAIR_CONTRAST_FREE_ROUTE_DECISION_JSON_FILENAME)
    forced_path = locate_batch_report(args.forced_choice, PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME)
    paths = {
        "corpus_contract": corpus_path,
        "v611": refresh_paths[0] if len(refresh_paths) > 0 else "",
        "v612": refresh_paths[1] if len(refresh_paths) > 1 else "",
        "v613": refresh_paths[2] if len(refresh_paths) > 2 else "",
        "comparison": comparison_path,
        "route_decision": route_path,
        "forced_choice": forced_path,
    }
    report = build_model_capability_required_term_pair_contrast_free_batch_closeout(
        corpus_contract=read_json_report(corpus_path),
        refresh_reports=[read_json_report(path) for path in refresh_paths],
        comparison=read_json_report(comparison_path),
        route_decision=read_json_report(route_path),
        forced_choice=read_json_report(forced_path),
        paths=paths,
    )
    outputs = write_model_capability_required_term_pair_contrast_free_batch_closeout_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_contrast_free_batch_closeout_text(report), end="")
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
