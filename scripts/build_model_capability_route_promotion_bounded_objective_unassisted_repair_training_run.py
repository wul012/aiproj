from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run import (  # noqa: E402
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run,
    locate_unassisted_repair_seed,
    read_json_report,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_training_run_artifacts import (  # noqa: E402
    render_bounded_objective_unassisted_repair_training_run_text,
    write_bounded_objective_unassisted_repair_training_run_outputs,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build evidence for a bounded objective unassisted repair training run.")
    parser.add_argument("--unassisted-repair-seed", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "model-capability-route-promotion-bounded-objective-unassisted-repair-training-run")
    parser.add_argument("--require-training-ready", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    seed_path = locate_unassisted_repair_seed(args.unassisted_repair_seed)
    prepare_output_dir(args.out_dir, force=args.force, preserve_dir=args.run_dir)
    report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_training_run(
        read_json_report(seed_path),
        args.run_dir,
        unassisted_repair_seed_path=seed_path,
    )
    outputs = write_bounded_objective_unassisted_repair_training_run_outputs(report, args.out_dir)
    print(render_bounded_objective_unassisted_repair_training_run_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    if resolve_exit_code(report, require_training_ready=args.require_training_ready):
        raise SystemExit(1)


def prepare_output_dir(out_dir: Path, *, force: bool, preserve_dir: Path | None = None) -> None:
    if out_dir.exists() and any(out_dir.iterdir()):
        if not force:
            raise SystemExit(f"output directory is not empty; pass --force to replace it: {out_dir}")
        if preserve_dir is not None and _is_relative_to(preserve_dir, out_dir):
            preserved = preserve_dir.resolve()
            for child in out_dir.iterdir():
                if child.resolve() == preserved:
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    main()
