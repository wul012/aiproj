from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe,
    locate_objective_replay_comparison,
    locate_objective_zero_hit_diagnostic,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe_artifacts import (  # noqa: E402
    render_bounded_objective_decoder_anchor_probe_text,
    write_bounded_objective_decoder_anchor_probe_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run decoder anchor probes against a bounded objective checkpoint.")
    parser.add_argument("--replay-comparison", type=Path, required=True, help="Bounded objective replay comparison JSON or output directory.")
    parser.add_argument("--zero-hit-diagnostic", type=Path, required=True, help="Bounded objective zero-hit diagnostic JSON or output directory.")
    parser.add_argument("--checkpoint", type=Path, required=True, help="MiniGPT checkpoint.pt used for probe generation.")
    parser.add_argument("--tokenizer", type=Path, default=None, help="Tokenizer JSON. Defaults to checkpoint parent tokenizer.json.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-decoder-anchor-probe")
    parser.add_argument("--require-probe-ready", action="store_true", help="Return exit code 1 when probe execution is not ready.")
    parser.add_argument("--require-anchor-success", action="store_true", help="Return exit code 1 unless an anchor-assisted completion signal appears.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    replay_path = locate_objective_replay_comparison(args.replay_comparison)
    diagnostic_path = locate_objective_zero_hit_diagnostic(args.zero_hit_diagnostic)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
        read_json_report(replay_path),
        read_json_report(diagnostic_path),
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        replay_comparison_path=replay_path,
        zero_hit_diagnostic_path=diagnostic_path,
    )
    outputs = write_bounded_objective_decoder_anchor_probe_outputs(report, args.out_dir)
    print(render_bounded_objective_decoder_anchor_probe_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    code = resolve_exit_code(
        report,
        require_probe_ready=args.require_probe_ready,
        require_anchor_success=args.require_anchor_success,
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
