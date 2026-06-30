"""Stable training import surface for MiniGPT workflows."""

from __future__ import annotations

from minigpt.training.corpus_setup import setup_single_corpus
from minigpt.training.data_prep import (
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
from minigpt.training.data_quality import (
    DatasetQualityIssue,
    build_dataset_quality_report,
    sha256_text,
    write_dataset_quality_json,
    write_dataset_quality_svg,
)
from minigpt.training.history import (
    TrainingRecord,
    append_record,
    load_records,
    summarize_records,
    write_loss_curve_svg,
)
from minigpt.training.lm import train_lm
from minigpt.training.runtime import choose_device, seed_everything

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
    "DatasetQualityIssue",
    "build_dataset_quality_report",
    "write_dataset_quality_json",
    "write_dataset_quality_svg",
    "sha256_text",
    "TrainingRecord",
    "append_record",
    "load_records",
    "summarize_records",
    "write_loss_curve_svg",
    "train_lm",
    "choose_device",
    "seed_everything",
    "setup_single_corpus",
]

