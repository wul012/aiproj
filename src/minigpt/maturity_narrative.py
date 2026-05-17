from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from minigpt.maturity_narrative_artifacts import (
    render_maturity_narrative_html,
    render_maturity_narrative_markdown,
    write_maturity_narrative_html,
    write_maturity_narrative_json,
    write_maturity_narrative_markdown,
    write_maturity_narrative_outputs,
)
from minigpt.maturity_narrative_sections import (
    build_maturity_narrative_evidence_matrix,
    build_maturity_narrative_sections,
)
from minigpt.maturity_narrative_summary import (
    build_maturity_narrative_recommendations,
    build_maturity_narrative_summary,
    build_maturity_narrative_warnings,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_maturity_narrative(
    project_root: str | Path,
    *,
    maturity_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    benchmark_scorecard_paths: list[str | Path] | None = None,
    benchmark_scorecard_decision_paths: list[str | Path] | None = None,
    dataset_card_paths: list[str | Path] | None = None,
    title: str = "MiniGPT release-quality maturity narrative",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    maturity_file = Path(maturity_path) if maturity_path is not None else root / "runs" / "maturity-summary" / "maturity_summary.json"
    registry_file = Path(registry_path) if registry_path is not None else root / "runs" / "registry" / "registry.json"
    request_file = (
        Path(request_history_summary_path)
        if request_history_summary_path is not None
        else root / "runs" / "request-history-summary" / "request_history_summary.json"
    )
    scorecard_files = [Path(path) for path in (benchmark_scorecard_paths or _discover_scorecards(root))]
    scorecard_decision_files = [Path(path) for path in (benchmark_scorecard_decision_paths or _discover_scorecard_decisions(root))]
    dataset_card_files = [Path(path) for path in (dataset_card_paths or _discover_dataset_cards(root))]

    maturity = _read_json(maturity_file)
    registry = _read_json(registry_file)
    request_history = _read_json(request_file)
    scorecards = [_read_json(path) for path in scorecard_files]
    scorecard_decisions = [_read_json(path) for path in scorecard_decision_files]
    dataset_cards = [_read_json(path) for path in dataset_card_files]

    summary = build_maturity_narrative_summary(maturity, registry, request_history, scorecards, scorecard_decisions, dataset_cards)
    sections = build_maturity_narrative_sections(summary)
    evidence = build_maturity_narrative_evidence_matrix(
        maturity_file,
        registry_file,
        request_file,
        scorecard_files,
        scorecard_decision_files,
        dataset_card_files,
        sections,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "project_root": str(root),
        "inputs": {
            "maturity_path": str(maturity_file),
            "registry_path": str(registry_file),
            "request_history_summary_path": str(request_file),
            "benchmark_scorecard_paths": [str(path) for path in scorecard_files],
            "benchmark_scorecard_decision_paths": [str(path) for path in scorecard_decision_files],
            "dataset_card_paths": [str(path) for path in dataset_card_files],
        },
        "summary": summary,
        "sections": sections,
        "evidence_matrix": evidence,
        "recommendations": build_maturity_narrative_recommendations(summary, sections),
        "warnings": build_maturity_narrative_warnings(maturity, registry, request_history, scorecards, dataset_cards),
    }


def _discover_scorecards(root: Path) -> list[Path]:
    return sorted(root.glob("runs/**/benchmark-scorecard/benchmark_scorecard.json"))


def _discover_scorecard_decisions(root: Path) -> list[Path]:
    return sorted(root.glob("runs/**/benchmark-scorecard-decision/benchmark_scorecard_decision.json"))


def _discover_dataset_cards(root: Path) -> list[Path]:
    return sorted(root.glob("datasets/**/dataset_card.json"))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None
