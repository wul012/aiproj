from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_required_term_pair_minimal_prompt_batch_closeout import (  # noqa: E402
    build_minimal_prompt_batch_closeout,
    locate_minimal_prompt_batch_report,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_batch_closeout_artifacts import (  # noqa: E402
    render_minimal_prompt_batch_closeout_text,
    write_minimal_prompt_batch_closeout_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Close out repeated minimal-prompt real training attempts.")
    parser.add_argument("--report", action="append", required=True, help="Label and report path in LABEL=PATH form. May be repeated.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-required-term-pair-minimal-prompt-batch-closeout")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when closeout checks fail.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    prepare_output_dir(args.out_dir, force=args.force)
    labels, sources = parse_report_args(args.report)
    reports = [read_json_report(source) for source in sources]
    report = build_minimal_prompt_batch_closeout(reports, labels=labels, paths=sources)
    outputs = write_minimal_prompt_batch_closeout_outputs(report, args.out_dir)
    print(render_minimal_prompt_batch_closeout_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_pass=args.require_pass):
        raise SystemExit(1)


def parse_report_args(values: list[str]) -> tuple[list[str], list[Path]]:
    labels: list[str] = []
    sources: list[Path] = []
    for value in values:
        if "=" in value:
            label, raw_path = value.split("=", 1)
        else:
            raw_path = value
            label = Path(value).stem
        source = locate_minimal_prompt_batch_report(raw_path)
        labels.append(label.strip() or source.parent.name)
        sources.append(source)
    return labels, sources


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
