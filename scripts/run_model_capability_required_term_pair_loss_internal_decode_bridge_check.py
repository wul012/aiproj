from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME  # noqa: E402
from minigpt.model_capability_required_term_pair_loss_internal_decode_bridge_check import (  # noqa: E402
    build_model_capability_required_term_pair_loss_internal_decode_bridge_check,
    locate_loss_internal_decode_bridge_input,
    read_loss_internal_decode_bridge_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_internal_decode_bridge_check_artifacts import (  # noqa: E402
    render_loss_internal_decode_bridge_check_text,
    write_loss_internal_decode_bridge_check_outputs,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_route_decision import (  # noqa: E402
    PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_refresh_forced_choice_diagnostic import (  # noqa: E402
    PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check internal-to-generation decode bridge gap for a selected route.")
    parser.add_argument("--refresh", type=Path, required=True)
    parser.add_argument("--forced-choice", type=Path, required=True)
    parser.add_argument("--route-decision", type=Path, required=True)
    parser.add_argument("--selected-source", default=None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-loss-internal-decode-bridge-check")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    refresh_path = locate_loss_internal_decode_bridge_input(args.refresh, PAIR_COEXISTENCE_REFRESH_JSON_FILENAME)
    forced_path = locate_loss_internal_decode_bridge_input(args.forced_choice, PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME)
    route_path = locate_loss_internal_decode_bridge_input(args.route_decision, PAIR_LOSS_INTERNAL_PREFERENCE_ROUTE_DECISION_JSON_FILENAME)
    report = build_model_capability_required_term_pair_loss_internal_decode_bridge_check(
        read_loss_internal_decode_bridge_input(refresh_path),
        read_loss_internal_decode_bridge_input(forced_path),
        read_loss_internal_decode_bridge_input(route_path),
        refresh_path=refresh_path,
        forced_choice_path=forced_path,
        route_decision_path=route_path,
        selected_source=args.selected_source,
    )
    outputs = write_loss_internal_decode_bridge_check_outputs(report, args.out_dir)
    print(render_loss_internal_decode_bridge_check_text(report), end="")
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
