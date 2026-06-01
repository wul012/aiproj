from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_policy_replay import (  # noqa: E402
    build_model_capability_required_term_pair_surface_policy_replay,
    locate_surface_policy_replay_plan_source,
    locate_surface_policy_replay_stability_source,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_policy_replay_artifacts import (  # noqa: E402
    render_surface_policy_replay_text,
    write_surface_policy_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay planned generation-surface policies over existing pair checkpoints.")
    parser.add_argument("stability", type=Path, help="Aligned-candidate seed stability JSON or directory.")
    parser.add_argument("policy_plan", type=Path, help="Surface policy plan JSON or directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-policy-replay")
    parser.add_argument("--max-new-tokens", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when replay fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    stability_source = locate_surface_policy_replay_stability_source(args.stability)
    policy_plan_source = locate_surface_policy_replay_plan_source(args.policy_plan)
    report = build_model_capability_required_term_pair_surface_policy_replay(
        read_json_report(stability_source),
        read_json_report(policy_plan_source),
        out_dir=args.out_dir,
        stability_source_path=stability_source,
        policy_plan_source_path=policy_plan_source,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        device=args.device,
    )
    outputs = write_surface_policy_replay_outputs(report, args.out_dir)
    print(render_surface_policy_replay_text(report), end="")
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
