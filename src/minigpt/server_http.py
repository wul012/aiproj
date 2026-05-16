from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from minigpt.server_contracts import sse_message


def read_json_body(handler: Any, max_body_bytes: int) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length > max_body_bytes:
        raise ValueError(f"request body must be at most {max_body_bytes} bytes")
    body = handler.rfile.read(length).decode("utf-8")
    payload = json.loads(body or "{}")
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    return payload


def send_json(handler: Any, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def send_text(
    handler: Any,
    text: str,
    *,
    content_type: str = "text/plain; charset=utf-8",
    filename: str | None = None,
    status: HTTPStatus = HTTPStatus.OK,
) -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    if filename is not None:
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    handler.end_headers()
    handler.wfile.write(body)


def send_sse_headers(handler: Any) -> None:
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "close")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()


def write_sse(handler: Any, event: str, data: dict[str, Any]) -> None:
    handler.wfile.write(sse_message(event, data))
    handler.wfile.flush()


def send_file(handler: Any, path: Path) -> None:
    body = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def serve_run_file(handler: Any, root: Path, request_path: str) -> None:
    relative = unquote(request_path.lstrip("/"))
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        send_json(handler, {"error": "not found"}, status=HTTPStatus.NOT_FOUND)
        return
    if not target.exists() or not target.is_file():
        send_json(handler, {"error": "not found"}, status=HTTPStatus.NOT_FOUND)
        return
    send_file(handler, target)


__all__ = [
    "read_json_body",
    "send_file",
    "send_json",
    "send_sse_headers",
    "send_text",
    "serve_run_file",
    "write_sse",
]
