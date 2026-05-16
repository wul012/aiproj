from __future__ import annotations

from functools import partial
import json
import mimetypes
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import monotonic
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from minigpt.pair_artifacts import (
    render_pair_generation_html as _render_pair_generation_html,
    write_pair_generation_artifacts as _write_pair_generation_artifacts,
)
from minigpt.request_history import (
    REQUEST_HISTORY_DEFAULT_LIMIT,
    REQUEST_HISTORY_MAX_LIMIT,
    append_inference_log,
    build_request_history_detail_payload,
    build_request_history_payload,
    query_value as _query_value,
    read_request_history_log_records,
    request_history_filters_from_query as _request_history_filters_from_query,
    request_history_limit_from_query as _request_history_limit_from_query,
    request_history_log_index_from_query as _request_history_log_index_from_query,
    request_history_to_csv,
)
from minigpt.server_contracts import (
    CheckpointOption,
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
    GenerationStreamChunk,
    InferenceSafetyProfile,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_health_payload,
    build_model_info_payload,
    discover_checkpoint_options,
    metadata_run_dir as _metadata_run_dir,
    pair_generation_payload as _pair_generation_payload,
    parse_generation_pair_request,
    parse_generation_request,
    resolve_checkpoint_option,
    sse_message,
    stream_timeout_payload,
)
from minigpt.server_generator import MiniGPTGenerator
from minigpt.server_logging import (
    build_generation_log_event,
    build_pair_generation_log_event,
)

from .playground import write_playground


def write_pair_generation_artifacts(
    run_dir: str | Path,
    payload: dict[str, Any],
    output_dir: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    return _write_pair_generation_artifacts(run_dir, payload, output_dir=output_dir, created_at=created_at)


def render_pair_generation_html(record: dict[str, Any]) -> str:
    return _render_pair_generation_html(record)


def create_handler(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    generator_factory: Callable[[str | Path, str | Path | None, str], Any] = MiniGPTGenerator,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> type[BaseHTTPRequestHandler]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    safety = safety_profile or InferenceSafetyProfile()
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"
    checkpoint_options = discover_checkpoint_options(root, checkpoint, tokenizer_path=tokenizer_path, checkpoint_candidates=checkpoint_candidates)
    generators: dict[str, Any] = {}

    def generator_for(option: CheckpointOption) -> Any:
        if option.id not in generators:
            selected_tokenizer = Path(option.tokenizer_path) if option.tokenizer_path is not None else tokenizer_path
            generators[option.id] = generator_factory(option.path, selected_tokenizer, device)
        return generators[option.id]

    class MiniGPTServerHandler(BaseHTTPRequestHandler):
        server_version = "MiniGPTServer/0.5"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._send_json(
                    build_health_payload(
                        root,
                        checkpoint,
                        safety_profile=safety,
                        request_log_path=request_log,
                        checkpoint_candidates=checkpoint_candidates,
                    )
                )
                return
            if parsed.path == "/api/checkpoints":
                self._send_json(build_checkpoints_payload(root, checkpoint, tokenizer_path, checkpoint_candidates))
                return
            if parsed.path == "/api/checkpoint-compare":
                self._send_json(build_checkpoint_compare_payload(root, checkpoint, tokenizer_path, checkpoint_candidates))
                return
            if parsed.path == "/api/request-history":
                try:
                    history_limit = _request_history_limit_from_query(parsed.query)
                    history_filters = _request_history_filters_from_query(parsed.query)
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                payload = build_request_history_payload(request_log, limit=history_limit, **history_filters)
                if _query_value(parsed.query, "format") == "csv":
                    self._send_text(
                        request_history_to_csv(payload["requests"]),
                        content_type="text/csv; charset=utf-8",
                        filename="request_history.csv",
                    )
                    return
                self._send_json(payload)
                return
            if parsed.path == "/api/request-history-detail":
                try:
                    log_index = _request_history_log_index_from_query(parsed.query)
                    payload = build_request_history_detail_payload(request_log, log_index)
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                except LookupError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    return
                self._send_json(payload)
                return
            if parsed.path == "/api/model-info":
                selector = _query_value(parsed.query, "checkpoint")
                try:
                    option = resolve_checkpoint_option(checkpoint_options, selector)
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(build_model_info_payload(_metadata_run_dir(root, option), option.path, option.tokenizer_path, option.id))
                return
            if parsed.path in {"/", "/playground.html"}:
                html_path = root / "playground.html"
                if not html_path.exists():
                    write_playground(root, output_path=html_path)
                self._send_file(html_path)
                return
            self._serve_run_file(parsed.path)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/generate-pair-artifact":
                self._handle_generate_pair(save_artifact=True)
                return
            if parsed.path == "/api/generate-pair":
                self._handle_generate_pair()
                return
            if parsed.path == "/api/generate-stream":
                self._handle_generate_stream()
                return
            if parsed.path != "/api/generate":
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            request: GenerationRequest | None = None
            option: CheckpointOption | None = None
            try:
                payload = self._read_json_body()
                request = parse_generation_request(payload, safety)
                option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
                if not option.exists:
                    raise ValueError(f"checkpoint does not exist: {option.id}")
                response = generator_for(option).generate(request)
            except ValueError as exc:
                self._log_generation("bad_request", request=request, checkpoint_option=option, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_generation("error", request=request, checkpoint_option=option, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._log_generation("ok", request=request, response=response, checkpoint_option=option)
            payload = response.to_dict()
            payload["checkpoint_id"] = option.id
            self._send_json(payload)

        def _handle_generate_stream(self) -> None:
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
                payload = self._read_json_body()
                request = parse_generation_request(payload, safety)
                option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
                if not option.exists:
                    raise ValueError(f"checkpoint does not exist: {option.id}")
                self._send_sse_headers()
                stream_open = True
                self._write_sse(
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
                    self._write_sse("token", chunk_payload)
                    elapsed_seconds = monotonic() - started_at
                    if elapsed_seconds >= safety.max_stream_seconds:
                        timed_out = True
                        self._write_sse(
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
                    self._write_sse(
                        "end",
                        {
                            "done": True,
                            "chunk_count": chunk_count,
                            "elapsed_seconds": round(elapsed_seconds, 6),
                            "response": response.to_dict(),
                        },
                    )
            except ValueError as exc:
                self._log_generation(
                    "bad_request",
                    request=request,
                    checkpoint_option=option,
                    error=str(exc),
                    endpoint="/api/generate-stream",
                )
                if stream_open:
                    self._write_sse("error", {"error": str(exc)})
                else:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
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
                self._log_generation(
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
                self._log_generation(
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
                    self._write_sse("error", {"error": str(exc)})
                else:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._log_generation(
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

        def _handle_generate_pair(self, *, save_artifact: bool = False) -> None:
            endpoint = "/api/generate-pair-artifact" if save_artifact else "/api/generate-pair"
            pair_request: GenerationPairRequest | None = None
            left_option: CheckpointOption | None = None
            right_option: CheckpointOption | None = None
            left_response: GenerationResponse | None = None
            right_response: GenerationResponse | None = None
            artifact: dict[str, Any] | None = None
            try:
                payload = self._read_json_body()
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
                self._log_pair_generation(
                    "bad_request",
                    pair_request=pair_request,
                    left_option=left_option,
                    right_option=right_option,
                    error=str(exc),
                    endpoint=endpoint,
                )
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_pair_generation(
                    "error",
                    pair_request=pair_request,
                    left_option=left_option,
                    right_option=right_option,
                    left_response=left_response,
                    right_response=right_response,
                    error=str(exc),
                    endpoint=endpoint,
                )
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            payload = _pair_generation_payload(pair_request, left_option, right_option, left_response, right_response)
            if save_artifact:
                artifact = write_pair_generation_artifacts(root, payload)
                payload["artifact"] = artifact
            self._log_pair_generation(
                "ok",
                pair_request=pair_request,
                left_option=left_option,
                right_option=right_option,
                left_response=left_response,
                right_response=right_response,
                artifact=artifact,
                endpoint=endpoint,
            )
            self._send_json(payload)

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _serve_run_file(self, request_path: str) -> None:
            relative = unquote(request_path.lstrip("/"))
            target = (root / relative).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            if not target.exists() or not target.is_file():
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_file(target)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length > safety.max_body_bytes:
                raise ValueError(f"request body must be at most {safety.max_body_bytes} bytes")
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body or "{}")
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _log_generation(
            self,
            status: str,
            *,
            request: GenerationRequest | None = None,
            response: GenerationResponse | None = None,
            checkpoint_option: CheckpointOption | None = None,
            error: str | None = None,
            endpoint: str = "/api/generate",
            stream_chunks: int | None = None,
            stream_timed_out: bool | None = None,
            stream_cancelled: bool | None = None,
            stream_elapsed_seconds: float | None = None,
        ) -> None:
            event = build_generation_log_event(
                status,
                endpoint=endpoint,
                client=self.client_address[0] if self.client_address else None,
                default_checkpoint=str(checkpoint),
                request=request,
                response=response,
                checkpoint_option=checkpoint_option,
                error=error,
                stream_chunks=stream_chunks,
                stream_timed_out=stream_timed_out,
                stream_cancelled=stream_cancelled,
                stream_elapsed_seconds=stream_elapsed_seconds,
            )
            append_inference_log(request_log, event)

        def _log_pair_generation(
            self,
            status: str,
            *,
            pair_request: GenerationPairRequest | None = None,
            left_option: CheckpointOption | None = None,
            right_option: CheckpointOption | None = None,
            left_response: GenerationResponse | None = None,
            right_response: GenerationResponse | None = None,
            artifact: dict[str, Any] | None = None,
            error: str | None = None,
            endpoint: str = "/api/generate-pair",
        ) -> None:
            event = build_pair_generation_log_event(
                status,
                endpoint=endpoint,
                client=self.client_address[0] if self.client_address else None,
                pair_request=pair_request,
                left_option=left_option,
                right_option=right_option,
                left_response=left_response,
                right_response=right_response,
                artifact=artifact,
                error=error,
            )
            append_inference_log(request_log, event)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _send_text(
            self,
            text: str,
            *,
            content_type: str = "text/plain; charset=utf-8",
            filename: str | None = None,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            if filename is not None:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def _send_sse_headers(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def _write_sse(self, event: str, data: dict[str, Any]) -> None:
            self.wfile.write(sse_message(event, data))
            self.wfile.flush()

        def _send_file(self, path: Path) -> None:
            body = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return MiniGPTServerHandler


def run_server(
    run_dir: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> ThreadingHTTPServer:
    handler = create_handler(
        run_dir,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        safety_profile=safety_profile,
        request_log_path=request_log_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    server = ThreadingHTTPServer((host, port), handler)
    return server
