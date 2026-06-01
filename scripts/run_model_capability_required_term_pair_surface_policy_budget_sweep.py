from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_surface_policy_budget_sweep import (  # noqa: E402
    DEFAULT_BUDGETS,
    build_surface_policy_budget_sweep,
    locate_budget_sweep_selector_source,
    locate_budget_sweep_stability_source,
    read_json_report,
    render_text,
    resolve_exit_code,
    write_surface_policy_budget_sweep_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sweep continuation budgets for the selected required-term pair surface policy.")
    parser.add_argument("stability", type=Path)
    parser.add_argument("selector", type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-surface-policy-budget-sweep")
    parser.add_argument("--budgets", type=int, nargs="+", default=list(DEFAULT_BUDGETS))
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    stability_source = locate_budget_sweep_stability_source(args.stability)
    selector_source = locate_budget_sweep_selector_source(args.selector)
    report = build_surface_policy_budget_sweep(
        read_json_report(stability_source),
        read_json_report(selector_source),
        out_dir=args.out_dir,
        stability_source_path=stability_source,
        selector_source_path=selector_source,
        token_budgets=tuple(args.budgets),
        temperature=args.temperature,
        top_k=args.top_k,
        device=args.device,
    )
    outputs = write_surface_policy_budget_sweep_outputs(report, args.out_dir)
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
