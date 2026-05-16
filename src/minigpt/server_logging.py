from __future__ import annotations

from typing import Any

from minigpt.server_contracts import (
    CheckpointOption,
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
)


def build_generation_log_event(
    status: str,
    *,
    endpoint: str = "/api/generate",
    client: str | None = None,
    default_checkpoint: str,
    request: GenerationRequest | None = None,
    response: GenerationResponse | None = None,
    checkpoint_option: CheckpointOption | None = None,
    error: str | None = None,
    stream_chunks: int | None = None,
    stream_timed_out: bool | None = None,
    stream_cancelled: bool | None = None,
    stream_elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "endpoint": endpoint,
        "status": status,
        "client": client,
        "checkpoint": checkpoint_option.path if checkpoint_option is not None else default_checkpoint,
        "checkpoint_id": checkpoint_option.id if checkpoint_option is not None else None,
    }
    if request is not None:
        event.update(
            {
                "requested_checkpoint": request.checkpoint,
                "prompt_chars": len(request.prompt),
                "max_new_tokens": request.max_new_tokens,
                "temperature": request.temperature,
                "top_k": request.top_k,
                "seed": request.seed,
            }
        )
    if response is not None:
        event["generated_chars"] = len(response.generated)
        event["continuation_chars"] = len(response.continuation)
        event["tokenizer"] = response.tokenizer
    if stream_chunks is not None:
        event["stream_chunks"] = stream_chunks
    if stream_timed_out is not None:
        event["stream_timed_out"] = stream_timed_out
    if stream_cancelled is not None:
        event["stream_cancelled"] = stream_cancelled
    if stream_elapsed_seconds is not None:
        event["stream_elapsed_seconds"] = round(stream_elapsed_seconds, 6)
    if error is not None:
        event["error"] = error
    return event


def build_pair_generation_log_event(
    status: str,
    *,
    endpoint: str = "/api/generate-pair",
    client: str | None = None,
    pair_request: GenerationPairRequest | None = None,
    left_option: CheckpointOption | None = None,
    right_option: CheckpointOption | None = None,
    left_response: GenerationResponse | None = None,
    right_response: GenerationResponse | None = None,
    artifact: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "endpoint": endpoint,
        "status": status,
        "client": client,
        "left_checkpoint": left_option.path if left_option is not None else None,
        "left_checkpoint_id": left_option.id if left_option is not None else None,
        "right_checkpoint": right_option.path if right_option is not None else None,
        "right_checkpoint_id": right_option.id if right_option is not None else None,
    }
    if pair_request is not None:
        event.update(
            {
                "requested_left_checkpoint": pair_request.left.checkpoint,
                "requested_right_checkpoint": pair_request.right.checkpoint,
                "prompt_chars": len(pair_request.left.prompt),
                "max_new_tokens": pair_request.left.max_new_tokens,
                "temperature": pair_request.left.temperature,
                "top_k": pair_request.left.top_k,
                "seed": pair_request.left.seed,
            }
        )
    if left_response is not None:
        event["left_generated_chars"] = len(left_response.generated)
        event["left_continuation_chars"] = len(left_response.continuation)
    if right_response is not None:
        event["right_generated_chars"] = len(right_response.generated)
        event["right_continuation_chars"] = len(right_response.continuation)
    if left_response is not None and right_response is not None:
        event["generated_equal"] = left_response.generated == right_response.generated
        event["continuation_equal"] = left_response.continuation == right_response.continuation
    if artifact is not None:
        event["artifact_json"] = artifact.get("json_path")
        event["artifact_html"] = artifact.get("html_path")
    if error is not None:
        event["error"] = error
    return event


__all__ = [
    "build_generation_log_event",
    "build_pair_generation_log_event",
]
