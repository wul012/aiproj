from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import utc_now


def write_pair_generation_artifacts(
    run_dir: str | Path,
    payload: dict[str, Any],
    output_dir: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    out_dir = Path(output_dir) if output_dir is not None else root / "pair_generations"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = created_at or utc_now()
    left_id = _as_dict(payload.get("left")).get("checkpoint_id") or "left"
    right_id = _as_dict(payload.get("right")).get("checkpoint_id") or "right"
    stem = unique_pair_artifact_stem(out_dir, f"{timestamp_slug(timestamp)}-{slug(left_id)}-vs-{slug(right_id)}")
    json_path = out_dir / f"{stem}.json"
    html_path = out_dir / f"{stem}.html"
    record = {
        "schema_version": 1,
        "kind": "minigpt_pair_generation",
        "created_at": timestamp,
        "run_dir": str(root),
        "request": {
            "prompt": payload.get("prompt"),
            "max_new_tokens": payload.get("max_new_tokens"),
            "temperature": payload.get("temperature"),
            "top_k": payload.get("top_k"),
            "seed": payload.get("seed"),
        },
        "left": payload.get("left"),
        "right": payload.get("right"),
        "comparison": payload.get("comparison"),
        "artifact": {
            "json_path": str(json_path),
            "html_path": str(html_path),
            "json_href": artifact_href(root, json_path),
            "html_href": artifact_href(root, html_path),
        },
    }
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_pair_generation_html(record), encoding="utf-8")
    return record["artifact"]


def render_pair_generation_html(record: dict[str, Any]) -> str:
    left = _as_dict(record.get("left"))
    right = _as_dict(record.get("right"))
    comparison = _as_dict(record.get("comparison"))
    request = _as_dict(record.get("request"))
    rows = [
        ("Created", record.get("created_at")),
        ("Prompt", request.get("prompt")),
        ("Max tokens", request.get("max_new_tokens")),
        ("Temperature", request.get("temperature")),
        ("Top-k", request.get("top_k")),
        ("Seed", request.get("seed")),
        ("Left checkpoint", left.get("checkpoint_id")),
        ("Right checkpoint", right.get("checkpoint_id")),
        ("Generated equal", comparison.get("generated_equal")),
        ("Generated char delta", comparison.get("generated_char_delta")),
        ("Continuation equal", comparison.get("continuation_equal")),
        ("Continuation char delta", comparison.get("continuation_char_delta")),
    ]
    table = "".join(f"<tr><th>{html_escape(label)}</th><td>{html_escape(value)}</td></tr>" for label, value in rows)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>MiniGPT pair generation {html_escape(record.get('created_at'))}</title>",
            "<style>",
            "body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;color:#172033;background:#f6f8fa;line-height:1.5}",
            "main{max-width:1100px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px}",
            "table{width:100%;border-collapse:collapse;margin:12px 0 18px}th,td{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}",
            ".grid{display:grid;grid-template-columns:repeat(2,minmax(260px,1fr));gap:14px}.panel{border:1px solid #d8dee4;border-radius:8px;padding:12px;background:#fbfcfd}",
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f7;border-radius:7px;padding:10px;min-height:120px}",
            "@media(max-width:760px){.grid{grid-template-columns:1fr}body{margin:12px}}",
            "</style>",
            "</head>",
            "<body><main>",
            "<h1>MiniGPT Pair Generation</h1>",
            f"<table>{table}</table>",
            '<section class="grid">',
            f"<article class=\"panel\"><h2>Left: {html_escape(left.get('checkpoint_id'))}</h2><pre>{html_escape(left.get('generated'))}</pre></article>",
            f"<article class=\"panel\"><h2>Right: {html_escape(right.get('checkpoint_id'))}</h2><pre>{html_escape(right.get('generated'))}</pre></article>",
            "</section>",
            "</main></body></html>",
        ]
    )


def artifact_href(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def timestamp_slug(value: str) -> str:
    return slug(value.replace("Z", "utc"))


def unique_pair_artifact_stem(out_dir: Path, base: str) -> str:
    stem = base or "pair-generation"
    candidate = stem
    index = 2
    while (out_dir / f"{candidate}.json").exists() or (out_dir / f"{candidate}.html").exists():
        candidate = f"{stem}-{index}"
        index += 1
    return candidate


def slug(value: Any) -> str:
    text = str(value).replace("\\", "/").strip().strip("/")
    output = []
    for char in text:
        if char.isalnum():
            output.append(char.lower())
        elif char in {"-", "_", ".", "/"}:
            output.append("-")
        else:
            output.append("-")
    result = "".join(output).strip("-")
    while "--" in result:
        result = result.replace("--", "-")
    return result or "checkpoint"


def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
