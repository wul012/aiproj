from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.generation_profile_contract_check import build_generation_profile_contract_check, resolve_exit_code  # noqa: E402
from minigpt.generation_profile_contract_check_artifacts import (  # noqa: E402
    render_generation_profile_contract_check_text,
    write_generation_profile_contract_check_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the MiniGPT generation profile endpoint/API/playground contract.")
    parser.add_argument("profiles", type=Path, help="Path to generation-profiles.json or its output directory.")
    parser.add_argument("--health", type=Path, required=True, help="Path to a health payload containing generation profile metadata.")
    parser.add_argument("--api-response", type=Path, required=True, help="Path to a suppression-profile /api/generate response JSON.")
    parser.add_argument("--playground-html", type=Path, required=True, help="Path to the playground HTML artifact.")
    parser.add_argument("--default-output", type=Path, required=True, help="Path to the archived default CLI generation output.")
    parser.add_argument("--profile-output", type=Path, required=True, help="Path to the archived suppression-profile CLI generation output.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "generation-profile-contract-check")
    parser.add_argument("--require-pass", action="store_true", help="Exit with 1 when any contract check fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_generation_profile_contract_check(
        args.profiles,
        health_path=args.health,
        api_response_path=args.api_response,
        playground_html_path=args.playground_html,
        default_output_path=args.default_output,
        profile_output_path=args.profile_output,
    )
    outputs = write_generation_profile_contract_check_outputs(report, args.out_dir)
    print(render_generation_profile_contract_check_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    exit_code = resolve_exit_code(report, require_pass=args.require_pass)
    if exit_code:
        raise SystemExit(exit_code)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
