from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.request_history import (  # noqa: E402
    append_inference_log,
    build_request_history_detail_payload,
    build_request_history_payload,
    read_inference_log_records,
    request_history_filters_from_query,
    request_history_limit_from_query,
    request_history_log_index_from_query,
    request_history_to_csv,
)


class RequestHistoryTests(unittest.TestCase):
    def test_history_payload_filters_recent_rows_and_counts_invalid_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(
                log_path,
                {"endpoint": "/api/generate", "status": "ok", "checkpoint_id": "default", "prompt_chars": 3},
            )
            log_path.write_text(log_path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-pair",
                    "status": "ok",
                    "left_checkpoint_id": "default",
                    "right_checkpoint_id": "candidate",
                    "generated_equal": False,
                },
            )
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "timeout",
                    "checkpoint_id": "candidate",
                    "stream_chunks": 2,
                    "stream_timed_out": True,
                },
            )

            payload = build_request_history_payload(log_path, limit=2, checkpoint_filter="candidate")

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["total_log_records"], 3)
            self.assertEqual(payload["matching_log_records"], 2)
            self.assertEqual(payload["invalid_record_count"], 1)
            self.assertEqual(payload["record_count"], 2)
            self.assertEqual(payload["requests"][0]["endpoint"], "/api/generate-stream")
            self.assertEqual(payload["requests"][1]["endpoint"], "/api/generate-pair")
            self.assertEqual(payload["summary"]["timeout_count"], 1)
            self.assertEqual(payload["summary"]["returned_status_counts"], {"timeout": 1, "ok": 1})

    def test_detail_payload_preserves_original_record_and_log_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(log_path, {"endpoint": "/api/generate", "status": "ok", "checkpoint_id": "default"})
            log_path.write_text(log_path.read_text(encoding="utf-8") + "[]\n", encoding="utf-8")
            append_inference_log(log_path, {"endpoint": "/api/generate-stream", "status": "cancelled", "stream_cancelled": True})

            detail = build_request_history_detail_payload(log_path, 3)

            self.assertEqual(detail["log_index"], 3)
            self.assertEqual(detail["invalid_record_count"], 1)
            self.assertEqual(detail["normalized"]["status"], "cancelled")
            self.assertTrue(detail["record"]["stream_cancelled"])
            with self.assertRaisesRegex(LookupError, "not found"):
                build_request_history_detail_payload(log_path, 2)

    def test_query_parsing_and_csv_export_keep_server_contract(self) -> None:
        filters = request_history_filters_from_query("status=ok&endpoint=%2Fapi%2Fgenerate&checkpoint=all")

        self.assertEqual(request_history_limit_from_query("limit=7"), 7)
        self.assertEqual(request_history_log_index_from_query("log_index=3"), 3)
        self.assertEqual(filters, {"status_filter": "ok", "endpoint_filter": "/api/generate", "checkpoint_filter": None})
        with self.assertRaisesRegex(ValueError, "limit"):
            request_history_limit_from_query("limit=999")
        with self.assertRaisesRegex(ValueError, "log_index"):
            request_history_log_index_from_query("")

        csv_text = request_history_to_csv(
            [
                {
                    "log_index": 1,
                    "endpoint": "/api/generate-pair",
                    "status": "ok",
                    "generated_equal": False,
                    "stream_timed_out": True,
                }
            ]
        )
        self.assertIn("log_index,timestamp,endpoint,status,checkpoint_id", csv_text)
        self.assertIn("false", csv_text)
        self.assertIn("true", csv_text)

    def test_raw_inference_log_reader_returns_records_without_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"endpoint": "/api/generate", "status": "ok", "generated": "not exported"}),
                        "{broken",
                        json.dumps(["not", "a", "record"]),
                    ]
                ),
                encoding="utf-8",
            )

            records, invalid_count = read_inference_log_records(log_path)

            self.assertEqual(invalid_count, 2)
            self.assertEqual(records, [{"endpoint": "/api/generate", "status": "ok", "generated": "not exported"}])


if __name__ == "__main__":
    unittest.main()
