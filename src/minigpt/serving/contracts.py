"""Compatibility exports for serving request and response contracts."""

from __future__ import annotations

from minigpt.server_contracts import (
    CheckpointOption,
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
    GenerationStreamChunk,
    InferenceSafetyProfile,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_generation_profiles_payload,
    build_health_payload,
    build_model_info_payload,
    discover_checkpoint_options,
    generation_profile_options,
    metadata_run_dir,
    pair_generation_payload,
    parse_generation_pair_request,
    parse_generation_request,
    resolve_checkpoint_option,
    sse_message,
    stream_timeout_payload,
)

__all__ = [
    "CheckpointOption",
    "GenerationPairRequest",
    "GenerationRequest",
    "GenerationResponse",
    "GenerationStreamChunk",
    "InferenceSafetyProfile",
    "build_checkpoint_compare_payload",
    "build_checkpoints_payload",
    "build_generation_profiles_payload",
    "build_health_payload",
    "build_model_info_payload",
    "discover_checkpoint_options",
    "generation_profile_options",
    "metadata_run_dir",
    "pair_generation_payload",
    "parse_generation_pair_request",
    "parse_generation_request",
    "resolve_checkpoint_option",
    "sse_message",
    "stream_timeout_payload",
]

