from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_generation_profile_replay import (  # noqa: E402
    DEFAULT_PROFILE_IDS,
    build_model_capability_required_term_pair_generation_profile_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_profile_replay_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_generation_profile_replay_text,
    write_model_capability_required_term_pair_generation_profile_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay generation profiles over archived fixed/loss pair checkpoints.")
    parser.add_argument("source", type=Path, help="Path to model_capability_required_term_pair_branch_retention_sweep.json.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-generation-profile-replay")
    parser.add_argument("--profiles", nargs="+", default=list(DEFAULT_PROFILE_IDS))
    parser.add_argument("--variant-limit", type=int, default=3)
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when replay execution fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_pair_generation_profile_replay(
        read_json_report(args.source),
        out_dir=args.out_dir,
        source_path=args.source,
        profiles=tuple(str(profile) for profile in args.profiles),
        variant_limit=args.variant_limit,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_generation_profile_replay_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_generation_profile_replay_text(report), end="")
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
