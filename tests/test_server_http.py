from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.server_http import (
    read_json_body,
    send_file,
    send_json,
    send_sse_headers,
    send_text,
    serve_run_file,
    write_sse,
)


class FakeHandler:
    def __init__(self, body: bytes = b"", headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {"Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status: HTTPStatus | None = None
        self.response_headers: list[tuple[str, str]] = []
        self.ended = False

    def send_response(self, status: HTTPStatus) -> None:
        self.status = status

    def send_header(self, name: str, value: str) -> None:
        self.response_headers.append((name, value))

    def end_headers(self) -> None:
        self.ended = True

    def header(self, name: str) -> str | None:
        for key, value in self.response_headers:
            if key.lower() == name.lower():
                return value
        return None


class ServerHttpTest(unittest.TestCase):
    def test_read_json_body_accepts_object_and_rejects_invalid_payloads(self) -> None:
        payload = read_json_body(FakeHandler(b'{"prompt":"hello"}'), max_body_bytes=64)
        self.assertEqual(payload, {"prompt": "hello"})

        with self.assertRaisesRegex(ValueError, "at most 4 bytes"):
            read_json_body(FakeHandler(b'{"too":"large"}'), max_body_bytes=4)

        with self.assertRaisesRegex(ValueError, "JSON object"):
            read_json_body(FakeHandler(b'["not-object"]'), max_body_bytes=64)

    def test_send_json_text_sse_and_file_helpers(self) -> None:
        json_handler = FakeHandler()
        send_json(json_handler, {"ok": True})
        self.assertEqual(json_handler.status, HTTPStatus.OK)
        self.assertEqual(json_handler.header("Content-Type"), "application/json; charset=utf-8")
        self.assertEqual(json.loads(json_handler.wfile.getvalue().decode("utf-8")), {"ok": True})

        text_handler = FakeHandler()
        send_text(text_handler, "a,b\n1,2", content_type="text/csv; charset=utf-8", filename="out.csv")
        self.assertEqual(text_handler.status, HTTPStatus.OK)
        self.assertEqual(text_handler.header("Content-Disposition"), 'attachment; filename="out.csv"')
        self.assertEqual(text_handler.wfile.getvalue().decode("utf-8"), "a,b\n1,2")

        sse_handler = FakeHandler()
        send_sse_headers(sse_handler)
        write_sse(sse_handler, "token", {"text": "x"})
        sse_body = sse_handler.wfile.getvalue().decode("utf-8")
        self.assertIn("event: token", sse_body)
        self.assertIn('"text": "x"', sse_body)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello", encoding="utf-8")
            file_handler = FakeHandler()
            send_file(file_handler, path)
            self.assertEqual(file_handler.status, HTTPStatus.OK)
            self.assertEqual(file_handler.header("Content-Type"), "text/plain")
            self.assertEqual(file_handler.wfile.getvalue(), b"hello")

    def test_serve_run_file_blocks_escape_and_serves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            root.mkdir()
            (root / "notes.txt").write_text("run note", encoding="utf-8")

            ok_handler = FakeHandler()
            serve_run_file(ok_handler, root, "/notes.txt")
            self.assertEqual(ok_handler.status, HTTPStatus.OK)
            self.assertEqual(ok_handler.wfile.getvalue(), b"run note")

            escape_handler = FakeHandler()
            serve_run_file(escape_handler, root, "/../secret.txt")
            self.assertEqual(escape_handler.status, HTTPStatus.NOT_FOUND)
            self.assertEqual(json.loads(escape_handler.wfile.getvalue().decode("utf-8")), {"error": "not found"})


if __name__ == "__main__":
    unittest.main()
