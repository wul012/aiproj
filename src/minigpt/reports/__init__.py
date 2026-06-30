"""Stable reports import surface for MiniGPT evidence artifacts."""

from __future__ import annotations

from minigpt.reports.artifact_map import (
    DEFAULT_LIMIT,
    build_artifact_map_report,
    resolve_exit_code,
    write_artifact_map_outputs,
)
from minigpt.reports.cards import (
    build_dataset_card,
    build_experiment_card,
    build_model_card,
    write_dataset_card_outputs,
    write_experiment_card_outputs,
    write_model_card_outputs,
)
from minigpt.reports.dashboard import (
    DashboardArtifact,
    build_dashboard_payload,
    collect_artifacts,
    render_dashboard_html,
    write_dashboard,
)
from minigpt.reports.manifest import (
    RUN_ARTIFACT_SPECS,
    build_environment_metadata,
    build_run_manifest,
    collect_git_metadata,
    collect_run_artifacts,
    sha256_file,
    utc_now,
    write_run_manifest_json,
    write_run_manifest_svg,
)
from minigpt.reports.model import (
    ParameterGroup,
    block_parameter_groups,
    build_model_report,
    count_parameters,
    output_head_is_tied,
    parameter_groups,
    tensor_shape_summary,
    write_model_report_svg,
)
from minigpt.reports.utils import write_output_bundle

__all__ = [
    "ParameterGroup",
    "count_parameters",
    "parameter_groups",
    "block_parameter_groups",
    "tensor_shape_summary",
    "output_head_is_tied",
    "build_model_report",
    "write_model_report_svg",
    "build_dataset_card",
    "build_experiment_card",
    "build_model_card",
    "write_dataset_card_outputs",
    "write_experiment_card_outputs",
    "write_model_card_outputs",
    "DashboardArtifact",
    "collect_artifacts",
    "build_dashboard_payload",
    "write_dashboard",
    "render_dashboard_html",
    "RUN_ARTIFACT_SPECS",
    "build_run_manifest",
    "build_environment_metadata",
    "collect_git_metadata",
    "collect_run_artifacts",
    "sha256_file",
    "write_run_manifest_json",
    "write_run_manifest_svg",
    "utc_now",
    "DEFAULT_LIMIT",
    "build_artifact_map_report",
    "write_artifact_map_outputs",
    "resolve_exit_code",
    "write_output_bundle",
]
