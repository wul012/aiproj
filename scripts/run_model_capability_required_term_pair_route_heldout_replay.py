from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_generation_profile_replay import DEFAULT_PROFILE_IDS  # noqa: E402
from minigpt.model_capability_required_term_pair_route_heldout_replay import (  # noqa: E402
    build_model_capability_required_term_pair_route_heldout_replay,
    locate_pair_route_decision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_heldout_replay import DEFAULT_HELDOUT_PROMPT_SPECS  # noqa: E402
from minigpt.model_capability_required_term_pair_route_heldout_replay_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_route_heldout_replay_text,
    write_model_capability_required_term_pair_route_heldout_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a selected route on held-out fixed/loss prompt surfaces.")
    parser.add_argument("route_decision", type=Path, help="Route-decision JSON file or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-route-heldout-replay")
    parser.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILE_IDS))
    parser.add_argument(
        "--prompt-spec",
        action="append",
        nargs=3,
        metavar=("SPEC_ID", "FIXED_PROMPT", "LOSS_PROMPT"),
        help="Held-out prompt spec. May be repeated. Defaults to the standard three-spec suite.",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when replay execution fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_pair_route_decision(args.route_decision)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_route_heldout_replay(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        prompt_specs=_prompt_specs(args.prompt_spec),
        profiles=tuple(str(profile) for profile in args.profiles),
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_route_heldout_replay_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_route_heldout_replay_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _prompt_specs(values: list[list[str]] | None) -> tuple[dict[str, str], ...]:
    if not values:
        return DEFAULT_HELDOUT_PROMPT_SPECS
    return tuple({"spec_id": spec_id, "fixed_prompt": fixed_prompt, "loss_prompt": loss_prompt} for spec_id, fixed_prompt, loss_prompt in values)


if __name__ == "__main__":
    main()
