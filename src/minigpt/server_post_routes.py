from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from time import monotonic
from typing import Any, Callable
from urllib.parse import urlparse

from minigpt.pair_artifacts import write_pair_generation_artifacts
from minigpt.server_contracts import (
    CheckpointOption,
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
    InferenceSafetyProfile,
    pair_generation_payload,
    parse_generation_pair_request,
    parse_generation_request,
    resolve_checkpoint_option,
    stream_timeout_payload,
)

GeneratorFor = Callable[[CheckpointOption], Any]


def handle_post_request(
    handler: Any,
    request_path: str,
    *,
    root: str | Path,
    checkpoint: str | Path,
    safety: InferenceSafetyProfile,
    checkpoint_options: list[CheckpointOption],
    generator_for: GeneratorFor,
) -> None:
    parsed = urlparse(request_path)
    if parsed.path == "/api/generate-pair-artifact":
        handle_generate_pair_request(
            handler,
            root=root,
            safety=safety,
            checkpoint_options=checkpoint_options,
            generator_for=generator_for,
            save_artifact=True,
        )
        return
    if parsed.path == "/api/generate-pair":
        handle_generate_pair_request(
            handler,
            root=root,
            safety=safety,
            checkpoint_options=checkpoint_options,
            generator_for=generator_for,
        )
        return
    if parsed.path == "/api/generate-stream":
        handle_generate_stream_request(
            handler,
            checkpoint=checkpoint,
            safety=safety,
            checkpoint_options=checkpoint_options,
            generator_for=generator_for,
        )
        return
    if parsed.path != "/api/generate":
        handler._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
        return
    handle_generate_request(
        handler,
        safety=safety,
        checkpoint_options=checkpoint_options,
        generator_for=generator_for,
    )


def handle_generate_request(
    handler: Any,
    *,
    safety: InferenceSafetyProfile,
    checkpoint_options: list[CheckpointOption],
    generator_for: GeneratorFor,
) -> None:
    request: GenerationRequest | None = None
    option: CheckpointOption | None = None
    try:
        payload = handler._read_json_body()
        request = parse_generation_request(payload, safety)
        option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
        if not option.exists:
            raise ValueError(f"checkpoint does not exist: {option.id}")
        response = generator_for(option).generate(request)
    except ValueError as exc:
        handler._log_generation("bad_request", request=request, checkpoint_option=option, error=str(exc))
        handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return
    except Exception as exc:
        handler._log_generation("error", request=request, checkpoint_option=option, error=str(exc))
        handler._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return
    handler._log_generation("ok", request=request, response=response, checkpoint_option=option)
    payload = response.to_dict()
    payload["checkpoint_id"] = option.id
    handler._send_json(payload)


def handle_generate_stream_request(
    handler: Any,
    *,
    checkpoint: str | Path,
    safety: InferenceSafetyProfile,
    checkpoint_options: list[CheckpointOption],
    generator_for: GeneratorFor,
) -> None:
    request: GenerationRequest | None = None
    option: CheckpointOption | None = None
    response: GenerationResponse | None = None
    chunk_count = 0
    stream_open = False
    timed_out = False
    cancelled = False
    elapsed_seconds = 0.0
    generated = ""
    continuation = ""
    tokenizer = "unknown"
    checkpoint_path = str(checkpoint)
    try:
        payload = handler._read_json_body()
        request = parse_generation_request(payload, safety)
        option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
        if not option.exists:
            raise ValueError(f"checkpoint does not exist: {option.id}")
        handler._send_sse_headers()
        stream_open = True
        handler._write_sse(
            "start",
            {
                "prompt": request.prompt,
                "max_new_tokens": request.max_new_tokens,
                "temperature": request.temperature,
                "top_k": request.top_k,
                "seed": request.seed,
                "checkpoint_id": option.id,
                "checkpoint": option.path,
                "max_stream_seconds": safety.max_stream_seconds,
            },
        )
        generated = request.prompt
        checkpoint_path = option.path
        started_at = monotonic()
        for chunk in generator_for(option).stream(request):
            chunk_count += 1
            chunk_payload = chunk.to_dict()
            chunk_payload["checkpoint_id"] = option.id
            generated = chunk.generated
            continuation = chunk.continuation
            tokenizer = chunk.tokenizer
            checkpoint_path = chunk.checkpoint
            handler._write_sse("token", chunk_payload)
            elapsed_seconds = monotonic() - started_at
            if elapsed_seconds >= safety.max_stream_seconds:
                timed_out = True
                handler._write_sse(
                    "timeout",
                    stream_timeout_payload(
                        request,
                        elapsed_seconds=elapsed_seconds,
                        max_stream_seconds=safety.max_stream_seconds,
                        chunk_count=chunk_count,
                        generated=generated,
                        continuation=continuation,
                        checkpoint=checkpoint_path,
                        tokenizer=tokenizer,
                        checkpoint_id=option.id,
                    ),
                )
                break
        response = GenerationResponse(
            prompt=request.prompt,
            generated=generated,
            continuation=continuation,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_k=request.top_k,
            seed=request.seed,
            checkpoint=checkpoint_path,
            tokenizer=tokenizer,
            checkpoint_id=option.id,
        )
        if not timed_out:
            elapsed_seconds = monotonic() - started_at
            handler._write_sse(
                "end",
                {
                    "done": True,
                    "chunk_count": chunk_count,
                    "elapsed_seconds": round(elapsed_seconds, 6),
                    "response": response.to_dict(),
                },
            )
    except ValueError as exc:
        handler._log_generation(
            "bad_request",
            request=request,
            checkpoint_option=option,
            error=str(exc),
            endpoint="/api/generate-stream",
        )
        if stream_open:
            handler._write_sse("error", {"error": str(exc)})
        else:
            handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
        cancelled = True
        if request is not None:
            response = GenerationResponse(
                prompt=request.prompt,
                generated=generated or request.prompt,
                continuation=continuation,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_k=request.top_k,
                seed=request.seed,
                checkpoint=checkpoint_path,
                tokenizer=tokenizer,
                checkpoint_id=option.id if option is not None else None,
            )
        handler._log_generation(
            "cancelled",
            request=request,
            response=response,
            checkpoint_option=option,
            endpoint="/api/generate-stream",
            stream_chunks=chunk_count,
            stream_timed_out=timed_out,
            stream_cancelled=cancelled,
            stream_elapsed_seconds=elapsed_seconds,
        )
        return
    except Exception as exc:
        handler._log_generation(
            "error",
            request=request,
            response=response,
            checkpoint_option=option,
            error=str(exc),
            endpoint="/api/generate-stream",
            stream_chunks=chunk_count,
            stream_timed_out=timed_out,
            stream_cancelled=cancelled,
            stream_elapsed_seconds=elapsed_seconds,
        )
        if stream_open:
            handler._write_sse("error", {"error": str(exc)})
        else:
            handler._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return
    handler._log_generation(
        "timeout" if timed_out else "ok",
        request=request,
        response=response,
        checkpoint_option=option,
        endpoint="/api/generate-stream",
        stream_chunks=chunk_count,
        stream_timed_out=timed_out,
        stream_cancelled=cancelled,
        stream_elapsed_seconds=elapsed_seconds,
    )


def handle_generate_pair_request(
    handler: Any,
    *,
    root: str | Path,
    safety: InferenceSafetyProfile,
    checkpoint_options: list[CheckpointOption],
    generator_for: GeneratorFor,
    save_artifact: bool = False,
) -> None:
    endpoint = "/api/generate-pair-artifact" if save_artifact else "/api/generate-pair"
    pair_request: GenerationPairRequest | None = None
    left_option: CheckpointOption | None = None
    right_option: CheckpointOption | None = None
    left_response: GenerationResponse | None = None
    right_response: GenerationResponse | None = None
    artifact: dict[str, Any] | None = None
    try:
        payload = handler._read_json_body()
        pair_request = parse_generation_pair_request(payload, safety)
        left_option = resolve_checkpoint_option(checkpoint_options, pair_request.left.checkpoint)
        right_option = resolve_checkpoint_option(checkpoint_options, pair_request.right.checkpoint)
        if not left_option.exists:
            raise ValueError(f"checkpoint does not exist: {left_option.id}")
        if not right_option.exists:
            raise ValueError(f"checkpoint does not exist: {right_option.id}")
        left_response = generator_for(left_option).generate(pair_request.left)
        right_response = generator_for(right_option).generate(pair_request.right)
    except ValueError as exc:
        handler._log_pair_generation(
            "bad_request",
            pair_request=pair_request,
            left_option=left_option,
            right_option=right_option,
            error=str(exc),
            endpoint=endpoint,
        )
        handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return
    except Exception as exc:
        handler._log_pair_generation(
            "error",
            pair_request=pair_request,
            left_option=left_option,
            right_option=right_option,
            left_response=left_response,
            right_response=right_response,
            error=str(exc),
            endpoint=endpoint,
        )
        handler._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return
    payload = pair_generation_payload(pair_request, left_option, right_option, left_response, right_response)
    if save_artifact:
        artifact = write_pair_generation_artifacts(root, payload)
        payload["artifact"] = artifact
    handler._log_pair_generation(
        "ok",
        pair_request=pair_request,
        left_option=left_option,
        right_option=right_option,
        left_response=left_response,
        right_response=right_response,
        artifact=artifact,
        endpoint=endpoint,
    )
    handler._send_json(payload)


__all__ = [
    "handle_generate_pair_request",
    "handle_generate_request",
    "handle_generate_stream_request",
    "handle_post_request",
]
