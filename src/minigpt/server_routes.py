from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from minigpt.playground import write_playground
from minigpt.request_history import query_value as _query_value
from minigpt.server_contracts import (
    CheckpointOption,
    InferenceSafetyProfile,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_health_payload,
    build_model_info_payload,
    metadata_run_dir,
    resolve_checkpoint_option,
)
from minigpt.server_request_history import (
    handle_request_history_detail_endpoint,
    handle_request_history_endpoint,
)


def handle_get_request(
    handler: Any,
    request_path: str,
    *,
    root: str | Path,
    checkpoint: str | Path,
    tokenizer_path: str | Path | None,
    safety: InferenceSafetyProfile,
    request_log: str | Path,
    checkpoint_candidates: list[str | Path] | None,
    checkpoint_options: list[CheckpointOption],
) -> None:
    parsed = urlparse(request_path)
    root_path = Path(root)
    if parsed.path == "/api/health":
        handler._send_json(
            build_health_payload(
                root_path,
                checkpoint,
                safety_profile=safety,
                request_log_path=request_log,
                checkpoint_candidates=checkpoint_candidates,
            )
        )
        return
    if parsed.path == "/api/checkpoints":
        handler._send_json(build_checkpoints_payload(root_path, checkpoint, tokenizer_path, checkpoint_candidates))
        return
    if parsed.path == "/api/checkpoint-compare":
        handler._send_json(build_checkpoint_compare_payload(root_path, checkpoint, tokenizer_path, checkpoint_candidates))
        return
    if parsed.path == "/api/request-history":
        handle_request_history_endpoint(handler, request_log, parsed.query)
        return
    if parsed.path == "/api/request-history-detail":
        handle_request_history_detail_endpoint(handler, request_log, parsed.query)
        return
    if parsed.path == "/api/model-info":
        selector = _query_value(parsed.query, "checkpoint")
        try:
            option = resolve_checkpoint_option(checkpoint_options, selector)
        except ValueError as exc:
            handler._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        handler._send_json(build_model_info_payload(metadata_run_dir(root_path, option), option.path, option.tokenizer_path, option.id))
        return
    if parsed.path in {"/", "/playground.html"}:
        html_path = root_path / "playground.html"
        if not html_path.exists():
            write_playground(root_path, output_path=html_path)
        handler._send_file(html_path)
        return
    handler._serve_run_file(parsed.path)


__all__ = [
    "handle_get_request",
]
