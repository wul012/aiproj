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
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (  # noqa: E402
    PAIR_PROBE_PROMPT_SPECS,
    build_fixed_preserving_transfer_pair_probe_replay,
    locate_fixed_preserving_transfer_pair_probe_replay_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay_artifacts import (  # noqa: E402
    render_fixed_preserving_transfer_pair_probe_replay_text,
    write_fixed_preserving_transfer_pair_probe_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a fixed-preserving transfer training run on heldout pair prompt surfaces.")
    parser.add_argument("training_run", type=Path, help="Training run JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-readiness-fixed-preserving-transfer-pair-probe-replay")
    parser.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILE_IDS))
    parser.add_argument(
        "--prompt-spec",
        action="append",
        nargs=3,
        metavar=("SPEC_ID", "PROMPT", "REQUIRED"),
        help="Pair prompt spec. REQUIRED is true/false. May be repeated.",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when replay execution fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_fixed_preserving_transfer_pair_probe_replay_source(args.training_run)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_fixed_preserving_transfer_pair_probe_replay(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        prompt_specs=_prompt_specs(args.prompt_spec),
        profiles=tuple(str(profile) for profile in args.profiles),
        device=args.device,
    )
    outputs = write_fixed_preserving_transfer_pair_probe_replay_outputs(report, args.out_dir)
    print(render_fixed_preserving_transfer_pair_probe_replay_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _prompt_specs(values: list[list[str]] | None) -> tuple[dict[str, object], ...]:
    if not values:
        return PAIR_PROBE_PROMPT_SPECS
    return tuple(
        {"spec_id": spec_id, "prompt": prompt, "required_for_ready": required.lower() in {"1", "true", "yes"}}
        for spec_id, prompt, required in values
    )


if __name__ == "__main__":
    main()
