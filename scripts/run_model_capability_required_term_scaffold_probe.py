from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_scaffold_probe import (  # noqa: E402
    build_model_capability_required_term_scaffold_probe,
    locate_model_capability_required_term_uptake,
    read_json_report,
)
from minigpt.model_capability_required_term_scaffold_probe_artifacts import (  # noqa: E402
    render_model_capability_required_term_scaffold_probe_text,
    write_model_capability_required_term_scaffold_probe_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scaffolded required-term generations from archived checkpoints.")
    parser.add_argument(
        "required_term_uptake",
        type=Path,
        help="Path to model_capability_required_term_uptake.json or its directory.",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-scaffold-probe")
    parser.add_argument("--max-new-tokens", type=int, default=24)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--generation-seed", type=int, default=482)
    parser.add_argument("--term-limit", type=int, default=1)
    parser.add_argument("--case-limit", type=int, default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the probe fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source = locate_model_capability_required_term_uptake(args.required_term_uptake)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_required_term_scaffold_probe(
        read_json_report(source),
        out_dir=args.out_dir,
        source_path=source,
        search_base=ROOT,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        generation_seed=args.generation_seed,
        term_limit=args.term_limit,
        case_limit=args.case_limit,
        device=args.device,
    )
    outputs = write_model_capability_required_term_scaffold_probe_outputs(report, args.out_dir)
    print(render_model_capability_required_term_scaffold_probe_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def resolve_exit_code(report: dict[str, object], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


if __name__ == "__main__":
    main()
