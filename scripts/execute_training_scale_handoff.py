from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_handoff import (  # noqa: E402
    build_training_scale_handoff,
    write_training_scale_handoff_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or execute a MiniGPT training scale workflow handoff command.")
    parser.add_argument("workflow", type=Path, help="training_scale_workflow.json file or workflow directory")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory; defaults to <workflow>/handoff")
    parser.add_argument("--execute", action="store_true", help="Run the generated --execute handoff command. Default only validates it.")
    parser.add_argument("--no-allow-review", action="store_true", help="Block review-status decisions instead of allowing them.")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--title", type=str, default="MiniGPT training scale execution handoff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workflow_path = Path(args.workflow)
    out_dir = args.out_dir or (_default_out_dir(workflow_path))
    report = build_training_scale_handoff(
        workflow_path,
        execute=args.execute,
        allow_review=not args.no_allow_review,
        timeout_seconds=args.timeout_seconds,
        title=args.title,
    )
    outputs = write_training_scale_handoff_outputs(report, out_dir)
    print(f"handoff_status={report.get('summary', {}).get('handoff_status')}")
    print(f"decision_status={report.get('decision_status')}")
    print(f"handoff_allowed={report.get('handoff_allowed')}")
    print(f"execute={report.get('execute')}")
    print(f"returncode={report.get('execution', {}).get('returncode')}")
    print("summary=" + json.dumps(report.get("summary", {}), ensure_ascii=False))
    print(f"command={report.get('command_text')}")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if report.get("summary", {}).get("handoff_status") in {"blocked", "failed", "timeout"}:
        raise SystemExit(1)


def _default_out_dir(path: Path) -> Path:
    if path.is_dir():
        return path / "handoff"
    return path.parent / "handoff"


if __name__ == "__main__":
    main()
