from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingRecord:
    step: int
    train_loss: float
    val_loss: float
    last_loss: float | None = None


def append_record(path: str | Path, record: TrainingRecord) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")


def load_records(path: str | Path) -> list[TrainingRecord]:
    history_path = Path(path)
    if not history_path.exists():
        return []

    records: list[TrainingRecord] = []
    for line_no, line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        try:
            records.append(
                TrainingRecord(
                    step=int(payload["step"]),
                    train_loss=float(payload["train_loss"]),
                    val_loss=float(payload["val_loss"]),
                    last_loss=None if payload.get("last_loss") is None else float(payload["last_loss"]),
                )
            )
        except KeyError as exc:
            raise ValueError(f"History record on line {line_no} is missing {exc}") from exc
    return records


def summarize_records(records: list[TrainingRecord]) -> dict[str, float | int | None]:
    if not records:
        return {
            "record_count": 0,
            "first_step": None,
            "last_step": None,
            "best_val_step": None,
            "best_val_loss": None,
            "last_train_loss": None,
            "last_val_loss": None,
        }

    best = min(records, key=lambda record: record.val_loss)
    last = records[-1]
    return {
        "record_count": len(records),
        "first_step": records[0].step,
        "last_step": last.step,
        "best_val_step": best.step,
        "best_val_loss": best.val_loss,
        "last_train_loss": last.train_loss,
        "last_val_loss": last.val_loss,
    }


def write_loss_curve_svg(records: list[TrainingRecord], path: str | Path, width: int = 820, height: int = 420) -> None:
    if not records:
        raise ValueError("Cannot write a loss curve without records")

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    margin_left = 64
    margin_right = 28
    margin_top = 32
    margin_bottom = 54
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    steps = [record.step for record in records]
    losses = [record.train_loss for record in records] + [record.val_loss for record in records]
    min_step, max_step = min(steps), max(steps)
    min_loss, max_loss = min(losses), max(losses)
    if min_step == max_step:
        max_step = min_step + 1
    if min_loss == max_loss:
        max_loss = min_loss + 1.0

    def xy(step: int, loss: float) -> tuple[float, float]:
        x = margin_left + (step - min_step) / (max_step - min_step) * plot_width
        y = margin_top + (max_loss - loss) / (max_loss - min_loss) * plot_height
        return x, y

    train_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(record.step, record.train_loss) for record in records))
    val_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in (xy(record.step, record.val_loss) for record in records))
    axis_x = margin_left
    axis_y = margin_top + plot_height
    best = min(records, key=lambda record: record.val_loss)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="{margin_left}" y="22" font-family="Arial, sans-serif" font-size="16" fill="#111827">MiniGPT loss curve</text>
  <line x1="{axis_x}" y1="{margin_top}" x2="{axis_x}" y2="{axis_y}" stroke="#374151" stroke-width="1"/>
  <line x1="{axis_x}" y1="{axis_y}" x2="{width - margin_right}" y2="{axis_y}" stroke="#374151" stroke-width="1"/>
  <polyline points="{train_points}" fill="none" stroke="#2563eb" stroke-width="3"/>
  <polyline points="{val_points}" fill="none" stroke="#dc2626" stroke-width="3"/>
  <text x="{margin_left}" y="{height - 22}" font-family="Arial, sans-serif" font-size="13" fill="#374151">step {min(steps)} to {max(steps)}</text>
  <text x="{width - 260}" y="{height - 22}" font-family="Arial, sans-serif" font-size="13" fill="#374151">best val: {best.val_loss:.4f} @ step {best.step}</text>
  <circle cx="{xy(best.step, best.val_loss)[0]:.1f}" cy="{xy(best.step, best.val_loss)[1]:.1f}" r="5" fill="#dc2626"/>
  <rect x="{width - 170}" y="30" width="130" height="54" rx="4" fill="#ffffff" stroke="#d1d5db"/>
  <line x1="{width - 156}" y1="50" x2="{width - 116}" y2="50" stroke="#2563eb" stroke-width="3"/>
  <text x="{width - 106}" y="54" font-family="Arial, sans-serif" font-size="13" fill="#111827">train</text>
  <line x1="{width - 156}" y1="72" x2="{width - 116}" y2="72" stroke="#dc2626" stroke-width="3"/>
  <text x="{width - 106}" y="76" font-family="Arial, sans-serif" font-size="13" fill="#111827">val</text>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")
