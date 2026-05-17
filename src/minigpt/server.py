from __future__ import annotations

from functools import partial
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from minigpt.pair_artifacts import (
    render_pair_generation_html as _render_pair_generation_html,
    write_pair_generation_artifacts as _write_pair_generation_artifacts,
)
from minigpt.request_history import (
    append_inference_log,
    build_request_history_detail_payload,
    build_request_history_payload,
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
    pair_generation_payload,
    parse_generation_pair_request,
    parse_generation_request,
    resolve_checkpoint_option,
    sse_message,
    stream_timeout_payload,
)
from minigpt.server_generator import MiniGPTGenerator
from minigpt.server_http import (
    read_json_body,
    send_file,
    send_json,
    send_sse_headers,
    send_text,
    serve_run_file,
    write_sse,
)
from minigpt.server_logging import (
    build_generation_log_event,
    build_pair_generation_log_event,
)
from minigpt.server_post_routes import handle_post_request
from minigpt.server_routes import handle_get_request

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
            handle_get_request(
                self,
                self.path,
                root=root,
                checkpoint=checkpoint,
                tokenizer_path=tokenizer_path,
                safety=safety,
                request_log=request_log,
                checkpoint_candidates=checkpoint_candidates,
                checkpoint_options=checkpoint_options,
            )

        def do_POST(self) -> None:
            handle_post_request(
                self,
                self.path,
                root=root,
                checkpoint=checkpoint,
                safety=safety,
                checkpoint_options=checkpoint_options,
                generator_for=generator_for,
            )

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _serve_run_file(self, request_path: str) -> None:
            serve_run_file(self, root, request_path)

        def _read_json_body(self) -> dict[str, Any]:
            return read_json_body(self, safety.max_body_bytes)

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
            send_json(self, payload, status=status)

        def _send_text(
            self,
            text: str,
            *,
            content_type: str = "text/plain; charset=utf-8",
            filename: str | None = None,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            send_text(self, text, content_type=content_type, filename=filename, status=status)

        def _send_sse_headers(self) -> None:
            send_sse_headers(self)

        def _write_sse(self, event: str, data: dict[str, Any]) -> None:
            write_sse(self, event, data)

        def _send_file(self, path: Path) -> None:
            send_file(self, path)

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
