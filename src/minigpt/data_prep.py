from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import html
import json
from pathlib import Path
from typing import Any


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


def write_prepared_dataset(
    dataset: PreparedDataset,
    out_dir: str | Path,
    output_name: str = "corpus.txt",
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    text_path = root / output_name
    json_path = root / "dataset_report.json"
    svg_path = root / "dataset_report.svg"
    quality_json_path = root / "dataset_quality.json"
    quality_svg_path = root / "dataset_quality.svg"
    text_path.write_text(dataset.text, encoding="utf-8")
    report = build_dataset_report(dataset, output_text=text_path)
    write_dataset_report_json(report, json_path)
    write_dataset_report_svg(report, svg_path)
    from minigpt.data_quality import build_dataset_quality_report, write_dataset_quality_json, write_dataset_quality_svg

    quality = build_dataset_quality_report(dataset)
    write_dataset_quality_json(quality, quality_json_path)
    write_dataset_quality_svg(quality, quality_svg_path)
    return {
        "text": str(text_path),
        "json": str(json_path),
        "svg": str(svg_path),
        "quality_json": str(quality_json_path),
        "quality_svg": str(quality_svg_path),
    }


def write_dataset_report_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


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
        rows.append(f'<text x="28" y="{y + 24}" font-family="Arial" font-size="13" fill="#111827">{html.escape(name)}</text>')
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
