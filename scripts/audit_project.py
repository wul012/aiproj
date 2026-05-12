from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.project_audit import build_project_audit, write_project_audit_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit MiniGPT registry/model-card readiness.")
    parser.add_argument("--registry", type=Path, default=ROOT / "runs" / "registry" / "registry.json")
    parser.add_argument("--model-card", type=Path, default=None, help="Optional model_card.json path")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory, defaults to the registry directory")
    parser.add_argument("--title", type=str, default="MiniGPT project audit")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero for warn as well as fail")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir or args.registry.parent
    audit = build_project_audit(args.registry, model_card_path=args.model_card, title=args.title)
    outputs = write_project_audit_outputs(audit, out_dir)
    summary = audit["summary"]

    print(f"registry={args.registry}")
    print(f"overall_status={summary['overall_status']}")
    print(f"score_percent={summary['score_percent']}")
    print(f"checks={summary['pass_count']} pass/{summary['warn_count']} warn/{summary['fail_count']} fail")
    print("outputs=" + json.dumps(outputs, ensure_ascii=False))
    if audit["warnings"]:
        print("warnings=" + json.dumps(audit["warnings"], ensure_ascii=False))
    if summary["overall_status"] == "fail" or (args.fail_on_warn and summary["overall_status"] == "warn"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
