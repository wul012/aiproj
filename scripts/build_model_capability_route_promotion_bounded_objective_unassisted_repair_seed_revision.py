from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision,
    locate_curriculum_revision,
    locate_objective_contract,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_artifacts import (  # noqa: E402
    render_bounded_objective_unassisted_repair_seed_revision_text,
    write_bounded_objective_unassisted_repair_seed_revision_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bounded objective unassisted repair seed revision corpus.")
    parser.add_argument("--curriculum-revision", type=Path, required=True)
    parser.add_argument("--objective-contract", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision")
    parser.add_argument("--require-seed-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    revision_path = locate_curriculum_revision(args.curriculum_revision)
    contract_path = locate_objective_contract(args.objective_contract)
    prepare_output_dir(args.out_dir, force=args.force)
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision(
        read_json_report(revision_path),
        read_json_report(contract_path),
        curriculum_revision_path=revision_path,
        objective_contract_path=contract_path,
    )
    outputs = write_bounded_objective_unassisted_repair_seed_revision_outputs(report, args.out_dir)
    print(render_bounded_objective_unassisted_repair_seed_revision_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_seed_ready=args.require_seed_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
