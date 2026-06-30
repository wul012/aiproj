from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_csv_rows import (
    handoff_csv_fieldnames,
    handoff_csv_row,
)
from minigpt.report_utils import write_csv_row


def write_promoted_training_scale_seed_handoff_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv_row(handoff_csv_row(report), out_path, handoff_csv_fieldnames())


__all__ = ["write_promoted_training_scale_seed_handoff_csv"]
