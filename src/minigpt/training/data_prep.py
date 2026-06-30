"""Compatibility exports for training data preparation."""

from __future__ import annotations

from minigpt.data_prep import (
    PreparedDataset,
    SourceFileSummary,
    build_dataset_report,
    build_dataset_snapshot,
    build_dataset_version_manifest,
    build_prepared_dataset,
    discover_text_files,
    normalize_text,
    render_dataset_version_html,
    write_dataset_report_json,
    write_dataset_report_svg,
    write_dataset_version_html,
    write_dataset_version_json,
    write_prepared_dataset,
)

__all__ = [
    "PreparedDataset",
    "SourceFileSummary",
    "discover_text_files",
    "normalize_text",
    "build_prepared_dataset",
    "build_dataset_report",
    "build_dataset_version_manifest",
    "write_prepared_dataset",
    "write_dataset_report_json",
    "write_dataset_report_svg",
    "write_dataset_version_json",
    "build_dataset_snapshot",
    "render_dataset_version_html",
    "write_dataset_version_html",
]

