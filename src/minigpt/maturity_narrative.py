from __future__ import annotations

from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_maturity_narrative(
    project_root: str | Path,
    *,
    maturity_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    benchmark_scorecard_paths: list[str | Path] | None = None,
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
    dataset_card_files = [Path(path) for path in (dataset_card_paths or _discover_dataset_cards(root))]

    maturity = _read_json(maturity_file)
    registry = _read_json(registry_file)
    request_history = _read_json(request_file)
    scorecards = [_read_json(path) for path in scorecard_files]
    dataset_cards = [_read_json(path) for path in dataset_card_files]

    summary = _summary(maturity, registry, request_history, scorecards, dataset_cards)
    sections = _sections(summary, maturity, registry, request_history, scorecards, dataset_cards)
    evidence = _evidence_matrix(
        maturity_file,
        registry_file,
        request_file,
        scorecard_files,
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
            "dataset_card_paths": [str(path) for path in dataset_card_files],
        },
        "summary": summary,
        "sections": sections,
        "evidence_matrix": evidence,
        "recommendations": _recommendations(summary, sections),
        "warnings": _warnings(maturity, registry, request_history, scorecards, dataset_cards),
    }


def write_maturity_narrative_json(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(narrative, ensure_ascii=False, indent=2), encoding="utf-8")


def render_maturity_narrative_markdown(narrative: dict[str, Any]) -> str:
    summary = _dict(narrative.get("summary"))
    lines = [
        f"# {narrative.get('title', 'MiniGPT release-quality maturity narrative')}",
        "",
        f"- Generated: `{narrative.get('generated_at')}`",
        f"- Project root: `{narrative.get('project_root')}`",
        "",
        "## Portfolio Summary",
        "",
        *_markdown_table(
            [
                ("Portfolio status", summary.get("portfolio_status")),
                ("Current version", summary.get("current_version")),
                ("Maturity status", summary.get("maturity_status")),
                ("Release readiness trend", summary.get("release_readiness_trend_status")),
                ("Request history status", summary.get("request_history_status")),
                ("Benchmark scorecards", summary.get("benchmark_scorecard_count")),
                ("Benchmark average", summary.get("benchmark_avg_score")),
                ("Dataset cards", summary.get("dataset_card_count")),
                ("Dataset warnings", summary.get("dataset_warning_count")),
            ]
        ),
        "",
        "## Narrative",
        "",
    ]
    for section in _list_of_dicts(narrative.get("sections")):
        lines.extend(
            [
                f"### {section.get('title')}",
                "",
                f"- Status: `{section.get('status')}`",
                f"- Claim: {section.get('claim')}",
                f"- Evidence: {section.get('evidence')}",
                f"- Boundary: {section.get('boundary')}",
                f"- Next step: {section.get('next_step')}",
                "",
            ]
        )
    lines.extend(["## Evidence Matrix", "", "| Area | Status | Evidence | Signal | Note |", "| --- | --- | --- | --- | --- |"])
    for item in _list_of_dicts(narrative.get("evidence_matrix")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("area")),
                    _md(item.get("status")),
                    _md(item.get("path")),
                    _md(item.get("signal")),
                    _md(item.get("note")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(narrative.get("recommendations")))
    warnings = _string_list(narrative.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_maturity_narrative_markdown(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_narrative_markdown(narrative), encoding="utf-8")


def render_maturity_narrative_html(narrative: dict[str, Any]) -> str:
    summary = _dict(narrative.get("summary"))
    stats = [
        ("Portfolio", summary.get("portfolio_status")),
        ("Version", summary.get("current_version")),
        ("Maturity", summary.get("maturity_status")),
        ("Release trend", summary.get("release_readiness_trend_status")),
        ("Requests", summary.get("request_history_status")),
        ("Benchmarks", summary.get("benchmark_scorecard_count")),
        ("Benchmark avg", summary.get("benchmark_avg_score")),
        ("Dataset cards", summary.get("dataset_card_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(narrative.get('title', 'MiniGPT release-quality maturity narrative'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(narrative.get('title', 'MiniGPT release-quality maturity narrative'))}</h1><p>{_e(narrative.get('project_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _section_cards(_list_of_dicts(narrative.get("sections"))),
            _evidence_table(_list_of_dicts(narrative.get("evidence_matrix"))),
            _list_section("Recommendations", narrative.get("recommendations")),
            _list_section("Warnings", narrative.get("warnings")),
            "<footer>Generated by MiniGPT maturity narrative exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maturity_narrative_html(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_narrative_html(narrative), encoding="utf-8")


def write_maturity_narrative_outputs(narrative: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maturity_narrative.json",
        "markdown": root / "maturity_narrative.md",
        "html": root / "maturity_narrative.html",
    }
    write_maturity_narrative_json(narrative, paths["json"])
    write_maturity_narrative_markdown(narrative, paths["markdown"])
    write_maturity_narrative_html(narrative, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _summary(
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
) -> dict[str, Any]:
    maturity_summary = _dict(_pick(maturity, "summary"))
    release = _release_summary(maturity_summary, _dict(_pick(maturity, "release_readiness_context")))
    request = _request_summary(maturity, request_history)
    benchmark_rows = [_scorecard_summary(item) for item in scorecards if isinstance(item, dict)]
    dataset_rows = [_dataset_summary(item) for item in dataset_cards if isinstance(item, dict)]
    benchmark_scores = [row["overall_score"] for row in benchmark_rows if row.get("overall_score") is not None]
    dataset_warnings = sum(int(row.get("warning_count") or 0) for row in dataset_rows)
    status = _portfolio_status(
        maturity_summary,
        release,
        request,
        benchmark_rows,
        dataset_rows,
        request_history_available=isinstance(request_history, dict),
    )
    return {
        "portfolio_status": status,
        "current_version": maturity_summary.get("current_version"),
        "maturity_status": maturity_summary.get("overall_status"),
        "average_maturity_level": maturity_summary.get("average_maturity_level"),
        "registry_runs": _coalesce(_pick(registry, "run_count"), maturity_summary.get("registry_runs")),
        "release_readiness_trend_status": release.get("trend_status"),
        "release_readiness_regressed_count": release.get("regressed_count"),
        "release_readiness_improved_count": release.get("improved_count"),
        "request_history_status": request.get("status"),
        "request_history_records": request.get("total_log_records"),
        "request_history_timeout_rate": request.get("timeout_rate"),
        "benchmark_scorecard_count": len(benchmark_rows),
        "benchmark_status_counts": _counts(row.get("overall_status") or "missing" for row in benchmark_rows),
        "benchmark_avg_score": round(sum(float(score) for score in benchmark_scores) / len(benchmark_scores), 2) if benchmark_scores else None,
        "benchmark_weakest_case": _weakest_benchmark_case(benchmark_rows),
        "dataset_card_count": len(dataset_rows),
        "dataset_status_counts": _counts(row.get("quality_status") or "missing" for row in dataset_rows),
        "dataset_warning_count": dataset_warnings,
    }


def _sections(
    summary: dict[str, Any],
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
) -> list[dict[str, Any]]:
    return [
        {
            "key": "maturity",
            "title": "Project Maturity",
            "status": summary.get("maturity_status") or "missing",
            "claim": f"MiniGPT is at v{summary.get('current_version')} with maturity level {summary.get('average_maturity_level')}.",
            "evidence": "maturity_summary.json captures version coverage, archives, capability matrix, registry context, request history, and release readiness trend.",
            "boundary": "This is a learning-engineering maturity view, not a claim of production model capability.",
            "next_step": "Turn the strongest evidence into a shorter release portfolio narrative.",
        },
        {
            "key": "release_quality",
            "title": "Release Quality Trend",
            "status": summary.get("release_readiness_trend_status") or "missing",
            "claim": _release_claim(summary),
            "evidence": "Registry-level release readiness comparison deltas are carried into maturity summary and then into this narrative.",
            "boundary": "The trend explains release evidence quality; it does not prove generated text quality.",
            "next_step": "Review regressions before release handoff; preserve improvement evidence when the trend is positive.",
        },
        {
            "key": "serving_stability",
            "title": "Local Serving Stability",
            "status": summary.get("request_history_status") or "missing",
            "claim": _request_claim(summary),
            "evidence": "request_history_summary.json records request counts, timeout/bad-request/error rates, endpoints, checkpoints, and recent requests.",
            "boundary": "Request history is local playground evidence and may not represent external traffic.",
            "next_step": "Keep request logs small, reproducible, and tied to checkpoint/model-info evidence.",
        },
        {
            "key": "benchmark_quality",
            "title": "Benchmark Quality",
            "status": _status_from_counts(summary.get("benchmark_status_counts")),
            "claim": _benchmark_claim(summary),
            "evidence": "Benchmark scorecards combine eval coverage, generation quality, rubric correctness, pair consistency, and evidence completeness.",
            "boundary": "Scorecards are deterministic review aids, not a substitute for larger benchmark suites.",
            "next_step": "Expand fixed prompts and compare larger or fine-tuned models when data size grows.",
        },
        {
            "key": "data_governance",
            "title": "Data Governance",
            "status": _status_from_counts(summary.get("dataset_status_counts")),
            "claim": _dataset_claim(summary),
            "evidence": "Dataset cards summarize dataset identity, provenance, quality status, warnings, artifacts, intended use, and limitations.",
            "boundary": "Dataset cards still require human review for licenses, consent, and domain fit.",
            "next_step": "Attach dataset cards to every meaningful training corpus before larger experiments.",
        },
        {
            "key": "portfolio_boundary",
            "title": "Portfolio Boundary",
            "status": summary.get("portfolio_status"),
            "claim": _portfolio_claim(summary),
            "evidence": "The narrative combines maturity, release trend, serving stability, benchmark scorecards, and dataset cards into one review surface.",
            "boundary": "The project remains a MiniGPT-from-scratch learning artifact, not a production LLM.",
            "next_step": "Use this narrative as the front door for demos, then link to detailed JSON/HTML evidence.",
        },
    ]


def _evidence_matrix(
    maturity_path: Path,
    registry_path: Path,
    request_path: Path,
    scorecard_paths: list[Path],
    dataset_card_paths: list[Path],
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        _evidence("maturity", "project maturity", maturity_path, sections[0]),
        _evidence("release quality", "release readiness trend", registry_path, sections[1]),
        _evidence("serving", "request history stability", request_path, sections[2]),
    ]
    for path in scorecard_paths:
        rows.append(_evidence("benchmark", "benchmark scorecard", path, sections[3]))
    for path in dataset_card_paths:
        rows.append(_evidence("dataset", "dataset card", path, sections[4]))
    return rows


def _evidence(area: str, signal: str, path: Path, section: dict[str, Any]) -> dict[str, Any]:
    return {
        "area": area,
        "status": section.get("status"),
        "path": str(path),
        "exists": path.exists(),
        "signal": signal,
        "note": section.get("claim"),
    }


def _recommendations(summary: dict[str, Any], sections: list[dict[str, Any]]) -> list[str]:
    if summary.get("portfolio_status") == "review":
        return ["Resolve review-level release, request-history, benchmark, or dataset concerns before using this as a release-ready portfolio summary."]
    if summary.get("portfolio_status") == "incomplete":
        return ["Generate missing maturity, request-history, benchmark scorecard, or dataset-card evidence before presenting the narrative."]
    return [
        "Use the narrative as the human-facing entry point, then link to maturity, registry, benchmark, dataset, and request-history artifacts for detail.",
        "Keep the next version focused on real model/data capability rather than another display-only report.",
    ]


def _warnings(
    maturity: dict[str, Any] | None,
    registry: dict[str, Any] | None,
    request_history: dict[str, Any] | None,
    scorecards: list[dict[str, Any] | None],
    dataset_cards: list[dict[str, Any] | None],
) -> list[str]:
    warnings = []
    if not isinstance(maturity, dict):
        warnings.append("maturity summary is missing")
    if not isinstance(registry, dict):
        warnings.append("registry is missing")
    if not isinstance(request_history, dict):
        warnings.append("request history summary is missing")
    if not any(isinstance(item, dict) for item in scorecards):
        warnings.append("benchmark scorecards are missing")
    if not any(isinstance(item, dict) for item in dataset_cards):
        warnings.append("dataset cards are missing")
    return warnings


def _portfolio_status(
    maturity: dict[str, Any],
    release: dict[str, Any],
    request: dict[str, Any],
    benchmark_rows: list[dict[str, Any]],
    dataset_rows: list[dict[str, Any]],
    *,
    request_history_available: bool,
) -> str:
    if not maturity or not benchmark_rows or not dataset_rows:
        return "incomplete"
    if not release.get("trend_status") or not request_history_available or not request:
        return "incomplete"
    if (
        maturity.get("overall_status") in {"warn", "fail"}
        or release.get("trend_status") == "regressed"
        or int(release.get("regressed_count") or 0) > 0
        or request.get("status") in {"watch", "warn", "fail"}
        or any(row.get("overall_status") in {"warn", "fail"} for row in benchmark_rows)
        or any(row.get("quality_status") in {"warn", "fail"} for row in dataset_rows)
    ):
        return "review"
    return "ready"


def _request_summary(maturity: dict[str, Any] | None, request_history: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(request_history, dict):
        return _dict(request_history.get("summary"))
    return _dict(_pick(maturity, "request_history_context"))


def _release_summary(maturity_summary: dict[str, Any], release_context: dict[str, Any]) -> dict[str, Any]:
    return {
        **release_context,
        "trend_status": _coalesce(release_context.get("trend_status"), maturity_summary.get("release_readiness_trend_status")),
        "regressed_count": _coalesce(release_context.get("regressed_count"), maturity_summary.get("release_readiness_regressed_count")),
        "improved_count": _coalesce(release_context.get("improved_count"), maturity_summary.get("release_readiness_improved_count")),
    }


def _scorecard_summary(scorecard: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(scorecard.get("summary"))
    return {
        "overall_status": summary.get("overall_status"),
        "overall_score": summary.get("overall_score"),
        "rubric_status": summary.get("rubric_status"),
        "rubric_avg_score": summary.get("rubric_avg_score"),
        "weakest_rubric_case": summary.get("weakest_rubric_case"),
        "weakest_rubric_score": summary.get("weakest_rubric_score"),
    }


def _dataset_summary(card: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(card.get("summary"))
    quality = _dict(card.get("quality"))
    return {
        "readiness_status": summary.get("readiness_status"),
        "quality_status": summary.get("quality_status") or quality.get("status"),
        "warning_count": summary.get("warning_count") or quality.get("warning_count"),
        "short_fingerprint": summary.get("short_fingerprint"),
    }


def _weakest_benchmark_case(rows: list[dict[str, Any]]) -> str | None:
    candidates = [row for row in rows if row.get("weakest_rubric_score") is not None]
    if not candidates:
        return None
    weakest = min(candidates, key=lambda item: float(item.get("weakest_rubric_score") or 0.0))
    return weakest.get("weakest_rubric_case")


def _status_from_counts(counts: Any) -> str:
    values = _dict(counts)
    if not values:
        return "missing"
    if int(values.get("fail") or 0) > 0:
        return "fail"
    if int(values.get("warn") or 0) > 0 or int(values.get("review") or 0) > 0:
        return "warn"
    if int(values.get("pass") or 0) > 0 or int(values.get("ready") or 0) > 0:
        return "pass"
    return sorted(values)[0]


def _release_claim(summary: dict[str, Any]) -> str:
    return (
        f"Release readiness trend is {summary.get('release_readiness_trend_status') or 'missing'} "
        f"with {summary.get('release_readiness_regressed_count') or 0} regression(s) and "
        f"{summary.get('release_readiness_improved_count') or 0} improvement(s)."
    )


def _request_claim(summary: dict[str, Any]) -> str:
    return (
        f"Request history status is {summary.get('request_history_status') or 'missing'} "
        f"across {summary.get('request_history_records') or 0} local inference records."
    )


def _benchmark_claim(summary: dict[str, Any]) -> str:
    return (
        f"{summary.get('benchmark_scorecard_count')} benchmark scorecard(s) are available; "
        f"average score is {summary.get('benchmark_avg_score') or 'missing'} and weakest case is "
        f"{summary.get('benchmark_weakest_case') or 'missing'}."
    )


def _dataset_claim(summary: dict[str, Any]) -> str:
    return (
        f"{summary.get('dataset_card_count')} dataset card(s) are available with "
        f"{summary.get('dataset_warning_count') or 0} warning(s)."
    )


def _portfolio_claim(summary: dict[str, Any]) -> str:
    return f"Portfolio status is {summary.get('portfolio_status')} after combining release, serving, benchmark, data, and maturity evidence."


def _discover_scorecards(root: Path) -> list[Path]:
    return sorted(root.glob("runs/**/benchmark-scorecard/benchmark_scorecard.json"))


def _discover_dataset_cards(root: Path) -> list[Path]:
    return sorted(root.glob("datasets/**/dataset_card.json"))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _section_cards(sections: list[dict[str, Any]]) -> str:
    cards = []
    for section in sections:
        cards.append(
            '<article class="panel narrative">'
            f"<h2>{_e(section.get('title'))}</h2>"
            f'<span class="pill {_e(section.get("status"))}">{_e(section.get("status"))}</span>'
            f"<p><strong>Claim.</strong> {_e(section.get('claim'))}</p>"
            f"<p><strong>Evidence.</strong> {_e(section.get('evidence'))}</p>"
            f"<p><strong>Boundary.</strong> {_e(section.get('boundary'))}</p>"
            f"<p><strong>Next.</strong> {_e(section.get('next_step'))}</p>"
            "</article>"
        )
    return "".join(cards)


def _evidence_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{_e(row.get('area'))}</td>"
        f"<td>{_e(row.get('status'))}</td>"
        f"<td>{_e(row.get('signal'))}</td>"
        f"<td>{_e(row.get('path'))}<br><span>exists={_e(row.get('exists'))}</span></td>"
        f"<td>{_e(row.get('note'))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        '<section class="panel"><h2>Evidence Matrix</h2>'
        '<table><thead><tr><th>Area</th><th>Status</th><th>Signal</th><th>Path</th><th>Note</th></tr></thead><tbody>'
        + body
        + "</tbody></table></section>"
    )


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values)
    if not items:
        return ""
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _style() -> str:
    return """<style>
:root { --ink:#151f2c; --muted:#566170; --line:#d8dee9; --page:#f7f8f3; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1f5f74; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.46; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
.narrative p { max-width:980px; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:62px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; background:var(--blue); }
.pill.ready, .pill.pass, .pill.improved, .pill.stable { background:var(--green); }
.pill.review, .pill.warn, .pill.panel-changed, .pill.incomplete { background:var(--amber); }
.pill.fail, .pill.regressed { background:var(--red); }
.pill.missing { background:#6b7280; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
