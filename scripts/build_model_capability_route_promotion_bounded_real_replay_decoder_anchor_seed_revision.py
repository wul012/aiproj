from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision,
    locate_policy_replay,
    locate_prompt_aligned_replay,
    locate_prompt_aligned_seed_revision,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build decoder-anchor-informed seed examples from bounded replay evidence.")
    parser.add_argument("--prompt-aligned-seed", type=Path, required=True, help="Prompt-aligned seed revision JSON or output directory.")
    parser.add_argument("--prompt-aligned-replay", type=Path, required=True, help="Prompt-aligned bounded replay JSON or output directory.")
    parser.add_argument("--policy-replay", type=Path, required=True, help="Decoder anchor policy replay JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-seed-revision")
    parser.add_argument("--require-seed-ready", action="store_true", help="Return exit code 1 when decoder anchor seed revision is not ready.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_prompt_aligned_seed_revision(args.prompt_aligned_seed)
    replay_path = locate_prompt_aligned_replay(args.prompt_aligned_replay)
    policy_replay_path = locate_policy_replay(args.policy_replay)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision(
        read_json_report(seed_path),
        read_json_report(replay_path),
        read_json_report(policy_replay_path),
        seed_revision_path=seed_path,
        replay_path=replay_path,
        policy_replay_path=policy_replay_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_seed_ready=args.require_seed_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
