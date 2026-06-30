"""Stable serving import surface for MiniGPT local generation."""

from __future__ import annotations

from minigpt.serving.checkpoints import (
    CheckpointOption,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_model_info_payload,
    discover_checkpoint_options,
    metadata_run_dir,
    resolve_checkpoint_option,
)
from minigpt.serving.chat import (
    ChatTurn,
    PreparedChatPrompt,
    assistant_reply_from_generation,
    build_chat_prompt,
    prepare_chat_prompt,
    turns_to_dicts,
)
from minigpt.serving.contracts import (
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
    GenerationStreamChunk,
    InferenceSafetyProfile,
    build_generation_profiles_payload,
    build_health_payload,
    generation_profile_options,
    pair_generation_payload,
    parse_generation_pair_request,
    parse_generation_request,
    sse_message,
    stream_timeout_payload,
)
from minigpt.serving.generator import MiniGPTGenerator
from minigpt.serving.profiles import GenerationProfile, generation_profile_ids
from minigpt.serving.server import create_handler, run_server

__all__ = [
    "CheckpointOption",
    "build_checkpoint_compare_payload",
    "build_checkpoints_payload",
    "build_model_info_payload",
    "discover_checkpoint_options",
    "metadata_run_dir",
    "resolve_checkpoint_option",
    "ChatTurn",
    "PreparedChatPrompt",
    "build_chat_prompt",
    "prepare_chat_prompt",
    "assistant_reply_from_generation",
    "turns_to_dicts",
    "GenerationPairRequest",
    "GenerationRequest",
    "GenerationResponse",
    "GenerationStreamChunk",
    "InferenceSafetyProfile",
    "build_generation_profiles_payload",
    "build_health_payload",
    "generation_profile_options",
    "pair_generation_payload",
    "parse_generation_pair_request",
    "parse_generation_request",
    "sse_message",
    "stream_timeout_payload",
    "MiniGPTGenerator",
    "GenerationProfile",
    "generation_profile_ids",
    "create_handler",
    "run_server",
]
