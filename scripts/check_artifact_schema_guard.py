from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts._bootstrap import PROJECT_ROOT, ensure_src_path
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT, ensure_src_path  # type: ignore[import-not-found,no-redef]

ensure_src_path()

from minigpt.artifact_schema_guard import (  # noqa: E402
    DEFAULT_SCHEMA_REGISTRY_PATH,
    build_artifact_schema_guard_report,
    resolve_exit_code,
    write_artifact_schema_guard_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check MiniGPT card and publication-receipt artifact schemas.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_SCHEMA_REGISTRY_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "runs" / "artifact-schema-guard")
    parser.add_argument("--require-pass", action="store_true", help="Return 1 when the schema guard fails.")
    parser.add_argument("--no-fail", action="store_true", help="Always return 0 after writing outputs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_artifact_schema_guard_report(args.registry, project_root=args.project_root)
    outputs = write_artifact_schema_guard_outputs(report, args.out_dir)
    summary = report["summary"]
    print(f"status={report['status']}")
    print(f"decision={report['decision']}")
    print(f"schema_count={summary['schema_count']}")
    print(f"artifact_count={summary['artifact_count']}")
    print(f"failed_check_count={summary['failed_check_count']}")
    print(f"outputs={json.dumps(outputs, ensure_ascii=False)}")
    if args.no_fail:
        return 0
    return resolve_exit_code(report, require_pass=args.require_pass or True)


if __name__ == "__main__":
    raise SystemExit(main())
