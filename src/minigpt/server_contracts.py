from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from minigpt.server_checkpoints import (
    CheckpointOption,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_health_payload as _build_checkpoint_health_payload,
    build_model_info_payload,
    discover_checkpoint_options,
    metadata_run_dir,
    resolve_checkpoint_option,
)


@dataclass(frozen=True)
class InferenceSafetyProfile:
    max_prompt_chars: int = 2000
    max_new_tokens: int = 512
    min_temperature: float = 0.05
    max_temperature: float = 2.0
    max_top_k: int = 200
    max_body_bytes: int = 16 * 1024
    max_stream_seconds: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int | None
    checkpoint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationPairRequest:
    left: GenerationRequest
    right: GenerationRequest

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(frozen=True)
class GenerationResponse:
    prompt: str
    generated: str
    continuation: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int | None
    checkpoint: str
    tokenizer: str
    checkpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationStreamChunk:
    index: int
    token_id: int | None
    text: str
    generated: str
    continuation: str
    checkpoint: str
    tokenizer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_generation_request(
    payload: dict[str, Any],
    safety_profile: InferenceSafetyProfile | None = None,
) -> GenerationRequest:
    safety = safety_profile or InferenceSafetyProfile()
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise ValueError("prompt cannot be empty")
    if len(prompt) > safety.max_prompt_chars:
        raise ValueError(f"prompt must be at most {safety.max_prompt_chars} characters")
    max_new_tokens = _as_int(payload.get("max_new_tokens", 80), "max_new_tokens")
    if max_new_tokens < 1 or max_new_tokens > safety.max_new_tokens:
        raise ValueError(f"max_new_tokens must be between 1 and {safety.max_new_tokens}")
    temperature = _as_float(payload.get("temperature", 0.8), "temperature")
    if temperature < safety.min_temperature or temperature > safety.max_temperature:
        raise ValueError(f"temperature must be between {safety.min_temperature:g} and {safety.max_temperature:g}")
    top_k_raw = payload.get("top_k", 30)
    top_k = None if _empty_top_k(top_k_raw) else _as_int(top_k_raw, "top_k")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be at least 1 when provided")
    if top_k is not None and top_k > safety.max_top_k:
        raise ValueError(f"top_k must be at most {safety.max_top_k}")
    seed_raw = payload.get("seed")
    seed = None if seed_raw in {None, ""} else _as_int(seed_raw, "seed")
    checkpoint_raw = payload.get("checkpoint")
    checkpoint = None if checkpoint_raw in {None, ""} else str(checkpoint_raw).strip()
    if checkpoint == "":
        checkpoint = None
    return GenerationRequest(
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        seed=seed,
        checkpoint=checkpoint,
    )


def parse_generation_pair_request(
    payload: dict[str, Any],
    safety_profile: InferenceSafetyProfile | None = None,
) -> GenerationPairRequest:
    left_selector = payload.get("left_checkpoint", payload.get("checkpoint"))
    right_selector = payload.get("right_checkpoint")
    if right_selector in {None, ""}:
        raise ValueError("right_checkpoint is required")
    left_payload = dict(payload)
    right_payload = dict(payload)
    left_payload["checkpoint"] = left_selector
    right_payload["checkpoint"] = right_selector
    return GenerationPairRequest(
        left=parse_generation_request(left_payload, safety_profile),
        right=parse_generation_request(right_payload, safety_profile),
    )


def build_health_payload(
    run_dir: str | Any,
    checkpoint_path: str | Any | None = None,
    *,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Any | None = None,
    checkpoint_candidates: list[str | Any] | None = None,
) -> dict[str, Any]:
    return _build_checkpoint_health_payload(
        run_dir,
        checkpoint_path,
        safety_profile=safety_profile or InferenceSafetyProfile(),
        request_log_path=request_log_path,
        checkpoint_candidates=checkpoint_candidates,
    )


def sse_message(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


def stream_timeout_payload(
    request: GenerationRequest,
    *,
    elapsed_seconds: float,
    max_stream_seconds: float,
    chunk_count: int,
    generated: str,
    continuation: str,
    checkpoint: str,
    tokenizer: str,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    response = GenerationResponse(
        prompt=request.prompt,
        generated=generated,
        continuation=continuation,
        max_new_tokens=request.max_new_tokens,
        temperature=request.temperature,
        top_k=request.top_k,
        seed=request.seed,
        checkpoint=checkpoint,
        tokenizer=tokenizer,
        checkpoint_id=checkpoint_id,
    )
    return {
        "done": False,
        "reason": "timeout",
        "elapsed_seconds": round(elapsed_seconds, 6),
        "max_stream_seconds": max_stream_seconds,
        "chunk_count": chunk_count,
        "response": response.to_dict(),
    }


def pair_generation_payload(
    pair_request: GenerationPairRequest,
    left_option: CheckpointOption,
    right_option: CheckpointOption,
    left_response: GenerationResponse,
    right_response: GenerationResponse,
) -> dict[str, Any]:
    left_payload = left_response.to_dict()
    right_payload = right_response.to_dict()
    left_payload["checkpoint_id"] = left_option.id
    right_payload["checkpoint_id"] = right_option.id
    return {
        "status": "ok",
        "prompt": pair_request.left.prompt,
        "max_new_tokens": pair_request.left.max_new_tokens,
        "temperature": pair_request.left.temperature,
        "top_k": pair_request.left.top_k,
        "seed": pair_request.left.seed,
        "left": left_payload,
        "right": right_payload,
        "comparison": {
            "same_checkpoint": left_option.id == right_option.id,
            "generated_equal": left_response.generated == right_response.generated,
            "continuation_equal": left_response.continuation == right_response.continuation,
            "left_generated_chars": len(left_response.generated),
            "right_generated_chars": len(right_response.generated),
            "generated_char_delta": len(right_response.generated) - len(left_response.generated),
            "left_continuation_chars": len(left_response.continuation),
            "right_continuation_chars": len(right_response.continuation),
            "continuation_char_delta": len(right_response.continuation) - len(left_response.continuation),
        },
    }


def _as_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def _empty_top_k(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in {"", "0", "none", "None"}
    return value == 0


__all__ = [
    "CheckpointOption",
    "GenerationPairRequest",
    "GenerationRequest",
    "GenerationResponse",
    "GenerationStreamChunk",
    "InferenceSafetyProfile",
    "build_checkpoint_compare_payload",
    "build_checkpoints_payload",
    "build_health_payload",
    "build_model_info_payload",
    "discover_checkpoint_options",
    "metadata_run_dir",
    "pair_generation_payload",
    "parse_generation_pair_request",
    "parse_generation_request",
    "resolve_checkpoint_option",
    "sse_message",
    "stream_timeout_payload",
]
