from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_policy_execution_profile import (  # noqa: E402
    build_surface_policy_execution_profile,
    locate_execution_profile_budget_source,
    locate_execution_profile_leakage_source,
    read_json_report,
    render_text,
    resolve_exit_code,
    write_surface_policy_execution_profile_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select an executable contextual surface policy profile.")
    parser.add_argument("leakage", type=Path)
    parser.add_argument("budget", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-policy-execution-profile")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    leakage_source = locate_execution_profile_leakage_source(args.leakage)
    budget_source = locate_execution_profile_budget_source(args.budget)
    report = build_surface_policy_execution_profile(
        read_json_report(leakage_source),
        read_json_report(budget_source),
        leakage_source_path=leakage_source,
        budget_source_path=budget_source,
    )
    outputs = write_surface_policy_execution_profile_outputs(report, args.out_dir)
    print(render_text(report), end="")
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
