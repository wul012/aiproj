from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict as _dict, html_escape as _e, utc_now, write_json_payload


@dataclass(frozen=True)
class SourceFileSummary:
    path: str
    char_count: int
    line_count: int
    nonempty_line_count: int
    unique_char_count: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreparedDataset:
    text: str
    sources: list[SourceFileSummary]

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def line_count(self) -> int:
        return len(self.text.splitlines())

    @property
    def unique_char_count(self) -> int:
        return len(set(self.text))

    @property
    def fingerprint(self) -> str:
        return _sha256_text(self.text)


def discover_text_files(sources: list[str | Path], recursive: bool = True) -> list[Path]:
    if not sources:
        raise ValueError("at least one source file or directory is required")
    files: list[Path] = []
    for source in sources:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*.txt" if recursive else "*.txt"
            files.extend(sorted(item for item in path.glob(pattern) if item.is_file()))
        else:
            raise ValueError(f"unsupported source path: {path}")
    unique = sorted({path.resolve(): path for path in files}.values(), key=lambda item: str(item))
    if not unique:
        raise ValueError("no .txt files found in dataset sources")
    return unique


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip("\n")


def build_prepared_dataset(sources: list[str | Path], recursive: bool = True) -> PreparedDataset:
    source_files = discover_text_files(sources, recursive=recursive)
    chunks: list[str] = []
    summaries: list[SourceFileSummary] = []
    for path in source_files:
        raw = path.read_text(encoding="utf-8")
        normalized = normalize_text(raw)
        summaries.append(_summarize_source(path, normalized))
        if normalized:
            chunks.append(normalized)
    if not chunks:
        raise ValueError("prepared dataset is empty after normalization")
    text = "\n\n".join(chunks) + "\n"
    return PreparedDataset(text=text, sources=summaries)


def build_dataset_report(dataset: PreparedDataset, output_text: str | Path | None = None) -> dict[str, Any]:
    most_common = [
        {"char": char, "count": count}
        for char, count in Counter(dataset.text).most_common(20)
        if char not in {"\n", "\t", " "}
    ][:12]
    return {
        "source_count": len(dataset.sources),
        "char_count": dataset.char_count,
        "line_count": dataset.line_count,
        "unique_char_count": dataset.unique_char_count,
        "token_count_char_estimate": dataset.char_count,
        "fingerprint": dataset.fingerprint,
        "output_text": None if output_text is None else str(output_text),
        "sources": [source.to_dict() for source in dataset.sources],
        "most_common_chars": most_common,
    }


def build_dataset_version_manifest(
    dataset: PreparedDataset,
    report: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    *,
    dataset_name: str = "dataset",
    dataset_version: str = "unversioned",
    description: str = "",
    source_roots: list[str | Path] | None = None,
    recursive: bool = True,
    output_name: str = "corpus.txt",
    outputs: dict[str, str] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    name = dataset_name.strip()
    version = dataset_version.strip()
    if not name:
        raise ValueError("dataset_name cannot be empty")
    if not version:
        raise ValueError("dataset_version cannot be empty")
    dataset_report = report or build_dataset_report(dataset)
    dataset_quality = quality if quality is not None else build_dataset_quality_report(dataset)
    fingerprint = str(dataset_report.get("fingerprint") or dataset.fingerprint)
    return {
        "schema_version": 1,
        "dataset": {
            "name": name,
            "version": version,
            "id": f"{name}@{version}",
            "description": description,
        },
        "created_at": created_at or _utc_now(),
        "preparation": {
            "recursive": bool(recursive),
            "output_name": output_name,
            "source_roots": [str(path) for path in (source_roots or [])],
        },
        "stats": {
            "source_count": len(dataset.sources),
            "char_count": dataset.char_count,
            "line_count": dataset.line_count,
            "unique_char_count": dataset.unique_char_count,
            "token_count_char_estimate": dataset.char_count,
            "fingerprint": fingerprint,
            "short_fingerprint": fingerprint[:12],
        },
        "quality": {
            "status": dataset_quality.get("status"),
            "warning_count": dataset_quality.get("warning_count"),
            "issue_count": dataset_quality.get("issue_count"),
            "duplicate_line_count": dataset_quality.get("duplicate_line_count"),
        },
        "outputs": dict(outputs or {}),
        "sources": [source.to_dict() for source in dataset.sources],
    }


def write_prepared_dataset(
    dataset: PreparedDataset,
    out_dir: str | Path,
    output_name: str = "corpus.txt",
    *,
    dataset_name: str = "dataset",
    dataset_version: str = "unversioned",
    dataset_description: str = "",
    source_roots: list[str | Path] | None = None,
    recursive: bool = True,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    text_path = root / output_name
    json_path = root / "dataset_report.json"
    svg_path = root / "dataset_report.svg"
    quality_json_path = root / "dataset_quality.json"
    quality_svg_path = root / "dataset_quality.svg"
    version_json_path = root / "dataset_version.json"
    version_html_path = root / "dataset_version.html"
    text_path.write_text(dataset.text, encoding="utf-8")
    report = build_dataset_report(dataset, output_text=text_path)
    write_dataset_report_json(report, json_path)
    write_dataset_report_svg(report, svg_path)
    from minigpt.data_quality import build_dataset_quality_report, write_dataset_quality_json, write_dataset_quality_svg

    quality = build_dataset_quality_report(dataset)
    write_dataset_quality_json(quality, quality_json_path)
    write_dataset_quality_svg(quality, quality_svg_path)
    outputs = {
        "text": str(text_path),
        "json": str(json_path),
        "svg": str(svg_path),
        "quality_json": str(quality_json_path),
        "quality_svg": str(quality_svg_path),
        "version_json": str(version_json_path),
        "version_html": str(version_html_path),
    }
    version_manifest = build_dataset_version_manifest(
        dataset,
        report,
        quality,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        description=dataset_description,
        source_roots=source_roots,
        recursive=recursive,
        output_name=output_name,
        outputs=outputs,
    )
    write_dataset_version_json(version_manifest, version_json_path)
    write_dataset_version_html(version_manifest, version_html_path)
    return outputs


def write_dataset_report_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_dataset_report_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sources = list(report.get("sources", []))
    width = 980
    row_h = 42
    top = 98
    height = top + max(1, len(sources)) * row_h + 84
    bar_x = 300
    bar_w = 480
    max_chars = max((int(source.get("char_count", 0)) for source in sources), default=1)
    rows: list[str] = []
    for index, source in enumerate(sources):
        y = top + index * row_h
        chars = int(source.get("char_count", 0))
        bar = 0 if max_chars == 0 else max(2, int(bar_w * chars / max_chars))
        name = _clip(Path(str(source.get("path", ""))).name, 34)
        rows.append(f'<text x="28" y="{y + 24}" font-family="Arial" font-size="13" fill="#111827">{_e(name)}</text>')
        rows.append(f'<rect x="{bar_x}" y="{y + 9}" width="{bar}" height="16" rx="3" fill="#047857"/>')
        rows.append(f'<text x="{bar_x + bar + 10}" y="{y + 22}" font-family="Arial" font-size="12" fill="#374151">{chars} chars</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT dataset report</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Sources: {report.get('source_count')} | Characters: {report.get('char_count')} | Unique chars: {report.get('unique_char_count')}</text>
  <text x="28" y="78" font-family="Arial" font-size="12" fill="#374151">Green bars compare character counts per source file.</text>
  {''.join(rows)}
</svg>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")


def write_dataset_version_json(manifest: dict[str, Any], path: str | Path) -> None:
    write_json_payload(manifest, path)


def render_dataset_version_html(manifest: dict[str, Any]) -> str:
    dataset = _dict(manifest.get("dataset"))
    stats = _dict(manifest.get("stats"))
    quality = _dict(manifest.get("quality"))
    preparation = _dict(manifest.get("preparation"))
    outputs = _dict(manifest.get("outputs"))
    cards = [
        ("Dataset", dataset.get("id")),
        ("Fingerprint", stats.get("short_fingerprint")),
        ("Sources", stats.get("source_count")),
        ("Characters", stats.get("char_count")),
        ("Quality", quality.get("status")),
        ("Warnings", quality.get("warning_count")),
        ("Recursive", preparation.get("recursive")),
        ("Created", manifest.get("created_at")),
    ]
    output_rows = "".join(
        f"<tr><td>{_e(key)}</td><td>{_e(value)}</td></tr>"
        for key, value in outputs.items()
    )
    source_rows = []
    for source in manifest.get("sources", [])[:24]:
        if isinstance(source, dict):
            source_rows.append(
                "<tr>"
                f"<td>{_e(Path(str(source.get('path'))).name)}</td>"
                f"<td>{_e(source.get('char_count'))}</td>"
                f"<td>{_e(source.get('line_count'))}</td>"
                f"<td>{_e(str(source.get('sha256', ''))[:12])}</td>"
                "</tr>"
            )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(dataset.get('id') or 'MiniGPT dataset version')}</title>",
            _html_style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(dataset.get('id') or 'MiniGPT dataset version')}</h1><p>{_e(dataset.get('description'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in cards) + "</section>",
            '<section class="panel"><h2>Outputs</h2><table><thead><tr><th>Key</th><th>Path</th></tr></thead><tbody>'
            + output_rows
            + "</tbody></table></section>",
            '<section class="panel"><h2>Sources</h2><table><thead><tr><th>File</th><th>Chars</th><th>Lines</th><th>SHA-256</th></tr></thead><tbody>'
            + "".join(source_rows)
            + "</tbody></table></section>",
            "<footer>Generated by MiniGPT dataset preparation.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_dataset_version_html(manifest: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dataset_version_html(manifest), encoding="utf-8")


def _summarize_source(path: Path, text: str) -> SourceFileSummary:
    lines = text.splitlines()
    return SourceFileSummary(
        path=str(path),
        char_count=len(text),
        line_count=len(lines),
        nonempty_line_count=sum(1 for line in lines if line.strip()),
        unique_char_count=len(set(text)),
        sha256=_sha256_text(text),
    )


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return utc_now()


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'


def _html_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f6f8fb; --panel:#ffffff; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:30px 36px 18px; background:#ffffff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
p { margin:0; color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; padding:18px 36px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.card { padding:14px 16px; min-height:74px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:16px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 36px; padding:18px; overflow:auto; }
table { width:100%; border-collapse:collapse; font-size:13px; }
th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#1f2937; background:#eef2f7; font-weight:700; }
footer { padding:12px 36px 28px; color:var(--muted); font-size:12px; }
</style>"""
