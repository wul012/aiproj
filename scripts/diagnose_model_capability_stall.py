from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_stall_diagnostic import (  # noqa: E402
    build_model_capability_stall_diagnostic,
    locate_stability_report,
    read_json_report,
)
from minigpt.model_capability_stall_diagnostic_artifacts import (  # noqa: E402
    render_model_capability_stall_diagnostic_text,
    write_model_capability_stall_diagnostic_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose why tiny model capability ladder scores stalled.")
    parser.add_argument("stability_report", type=Path, help="Path to model_capability_ladder_stability.json or its directory.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-stall-diagnostic")
    parser.add_argument("--require-pass", action="store_true", help="Return exit code 1 when the diagnostic fails.")
    parser.add_argument("--force", action="store_true", help="Delete an existing non-empty output directory first.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    source_path = locate_stability_report(args.stability_report)
    prepare_output_dir(args.out_dir, force=args.force)
    stability = read_json_report(source_path)
    report = build_model_capability_stall_diagnostic(
        stability,
        out_dir=args.out_dir,
        source_path=source_path,
        search_base=ROOT,
    )
    outputs = write_model_capability_stall_diagnostic_outputs(report, args.out_dir)
    print(render_model_capability_stall_diagnostic_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if args.require_pass and report.get("status") != "pass":
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
