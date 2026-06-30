"""Compatibility exports for model architecture reports."""

from __future__ import annotations

from minigpt.model_report import (
    ParameterGroup,
    block_parameter_groups,
    build_model_report,
    count_parameters,
    output_head_is_tied,
    parameter_groups,
    tensor_shape_summary,
    write_model_report_svg,
)

__all__ = [
    "ParameterGroup",
    "count_parameters",
    "parameter_groups",
    "block_parameter_groups",
    "tensor_shape_summary",
    "output_head_is_tied",
    "build_model_report",
    "write_model_report_svg",
]
