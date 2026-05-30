from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_first_token_preference import (  # noqa: E402
    build_model_capability_required_term_pair_first_token_preference,
    locate_pair_coexistence_refresh,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_first_token_preference_artifacts import (  # noqa: E402
    render_model_capability_required_term_pair_first_token_preference_text,
    write_model_capability_required_term_pair_first_token_preference_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score first-token preferences for a fixed/loss pair refresh checkpoint.")
    parser.add_argument("refresh", type=Path, help="Path to v533 pair coexistence refresh JSON or output directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-first-token-preference")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when diagnostic execution fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    source = locate_pair_coexistence_refresh(args.refresh)
    report = build_model_capability_required_term_pair_first_token_preference(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        top_k=args.top_k,
        device=args.device,
    )
    outputs = write_model_capability_required_term_pair_first_token_preference_outputs(report, args.out_dir)
    print(render_model_capability_required_term_pair_first_token_preference_text(report), end="")
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
