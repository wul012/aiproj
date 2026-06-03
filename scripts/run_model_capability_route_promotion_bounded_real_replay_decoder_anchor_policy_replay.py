from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay import (  # noqa: E402
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay,
    locate_decoder_anchor_policy,
    locate_prompt_aligned_replay,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_artifacts import (  # noqa: E402
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay a guarded decoder anchor policy against bounded replay cases.")
    parser.add_argument("--prompt-aligned-replay", type=Path, required=True, help="Prompt-aligned bounded replay JSON or output directory.")
    parser.add_argument("--decoder-anchor-policy", type=Path, required=True, help="Decoder anchor policy JSON or output directory.")
    parser.add_argument("--checkpoint", type=Path, required=True, help="MiniGPT checkpoint.pt used for policy replay.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Tokenizer JSON. Defaults to checkpoint parent tokenizer.json.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-real-replay-decoder-anchor-policy-replay")
    parser.add_argument("--require-replay-ready", action="store_true", help="Return exit code 1 when policy replay execution is not ready.")
    parser.add_argument("--require-policy-case-pass", action="store_true", help="Return exit code 1 unless at least one policy-applied case passes.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_prompt_aligned_replay(args.prompt_aligned_replay)
    policy_path = locate_decoder_anchor_policy(args.decoder_anchor_policy)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay(
        read_json_report(replay_path),
        read_json_report(policy_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        replay_path=replay_path,
        policy_path=policy_path,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs(report, args.out_dir)
    print(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_replay_ready=args.require_replay_ready,
        require_policy_case_pass=args.require_policy_case_pass,
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
