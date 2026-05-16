from __future__ import annotations

import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.request_history import append_inference_log
from minigpt.server_request_history import (
    handle_request_history_detail_endpoint,
    handle_request_history_endpoint,
)


class FakeHistoryHandler:
    def __init__(self) -> None:
        self.json_payload: dict | None = None
        self.text_payload: str | None = None
        self.status: HTTPStatus | None = None
        self.content_type: str | None = None
        self.filename: str | None = None

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.json_payload = payload
        self.status = status

    def _send_text(
        self,
        text: str,
        *,
        content_type: str = "text/plain; charset=utf-8",
        filename: str | None = None,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.text_payload = text
        self.content_type = content_type
        self.filename = filename
        self.status = status


class ServerRequestHistoryEndpointTests(unittest.TestCase):
    def test_history_endpoint_returns_json_csv_and_bad_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(log_path, {"endpoint": "/api/generate", "status": "ok", "checkpoint_id": "default"})
            append_inference_log(log_path, {"endpoint": "/api/generate-stream", "status": "timeout", "checkpoint_id": "candidate"})

            json_handler = FakeHistoryHandler()
            handle_request_history_endpoint(json_handler, log_path, "limit=1&checkpoint=candidate")
            self.assertEqual(json_handler.status, HTTPStatus.OK)
            self.assertEqual(json_handler.json_payload["record_count"], 1)
            self.assertEqual(json_handler.json_payload["requests"][0]["checkpoint_id"], "candidate")

            csv_handler = FakeHistoryHandler()
            handle_request_history_endpoint(csv_handler, log_path, "format=csv&status=ok")
            self.assertEqual(csv_handler.status, HTTPStatus.OK)
            self.assertEqual(csv_handler.content_type, "text/csv; charset=utf-8")
            self.assertEqual(csv_handler.filename, "request_history.csv")
            self.assertIn("log_index,timestamp,endpoint,status,checkpoint_id", csv_handler.text_payload)

            error_handler = FakeHistoryHandler()
            handle_request_history_endpoint(error_handler, log_path, "limit=999")
            self.assertEqual(error_handler.status, HTTPStatus.BAD_REQUEST)
            self.assertIn("limit", error_handler.json_payload["error"])

    def test_history_detail_endpoint_maps_bad_request_and_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(log_path, {"endpoint": "/api/generate", "status": "ok", "checkpoint_id": "default"})

            ok_handler = FakeHistoryHandler()
            handle_request_history_detail_endpoint(ok_handler, log_path, "log_index=1")
            self.assertEqual(ok_handler.status, HTTPStatus.OK)
            self.assertEqual(ok_handler.json_payload["log_index"], 1)
            self.assertEqual(ok_handler.json_payload["record"]["checkpoint_id"], "default")

            bad_handler = FakeHistoryHandler()
            handle_request_history_detail_endpoint(bad_handler, log_path, "")
            self.assertEqual(bad_handler.status, HTTPStatus.BAD_REQUEST)
            self.assertIn("log_index", bad_handler.json_payload["error"])

            missing_handler = FakeHistoryHandler()
            handle_request_history_detail_endpoint(missing_handler, log_path, "log_index=9")
            self.assertEqual(missing_handler.status, HTTPStatus.NOT_FOUND)
            self.assertIn("not found", missing_handler.json_payload["error"])


if __name__ == "__main__":
    unittest.main()
