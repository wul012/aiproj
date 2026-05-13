from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.request_history_summary import (
    build_request_history_summary,
    render_request_history_summary_html,
    write_request_history_summary_outputs,
)
from minigpt.server import append_inference_log


class RequestHistorySummaryTests(unittest.TestCase):
    def test_build_request_history_summary_counts_statuses_and_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "inference_requests.jsonl"
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate",
                    "status": "ok",
                    "checkpoint_id": "default",
                    "prompt_chars": 3,
                    "generated_chars": 8,
                },
            )
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "timeout",
                    "checkpoint_id": "wide",
                    "prompt_chars": 4,
                    "stream_chunks": 2,
                    "stream_timed_out": True,
                },
            )
            log_path.write_text(log_path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-pair-artifact",
                    "status": "bad_request",
                    "left_checkpoint_id": "default",
                    "right_checkpoint_id": "wide",
                    "artifact_json": "pair_generations/demo.json",
                    "artifact_html": "pair_generations/demo.html",
                },
            )

            report = build_request_history_summary(log_path, generated_at="2026-05-13T00:00:00Z")
            summary = report["summary"]

            self.assertEqual(summary["status"], "review")
            self.assertEqual(summary["total_log_records"], 3)
            self.assertEqual(summary["invalid_record_count"], 1)
            self.assertEqual(summary["ok_count"], 1)
            self.assertEqual(summary["timeout_count"], 1)
            self.assertEqual(summary["bad_request_count"], 1)
            self.assertEqual(summary["timeout_rate"], 0.3333)
            self.assertEqual(summary["bad_request_rate"], 0.3333)
            self.assertEqual(summary["stream_request_count"], 1)
            self.assertEqual(summary["pair_request_count"], 1)
            self.assertEqual(summary["artifact_request_count"], 1)
            self.assertEqual(summary["unique_checkpoint_count"], 2)
            self.assertEqual(report["checkpoint_counts"]["default"], 2)
            self.assertEqual(report["checkpoint_counts"]["wide"], 2)
            self.assertEqual(report["recent_requests"][0]["log_index"], 4)
            self.assertIn("Review failed or bad-request rows", " ".join(report["recommendations"]))

    def test_write_request_history_summary_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "requests.jsonl"
            append_inference_log(log_path, {"endpoint": "/api/generate", "status": "ok", "checkpoint_id": "default"})
            report = build_request_history_summary(log_path)

            outputs = write_request_history_summary_outputs(report, root / "summary")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("timeout_rate", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("Request history is clean", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            loaded = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(loaded["summary"]["status"], "pass")

    def test_render_request_history_summary_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(log_path, {"endpoint": "<api>", "status": "ok", "checkpoint_id": "<default>"})
            report = build_request_history_summary(log_path, title="<History>")

            html = render_request_history_summary_html(report)

            self.assertIn("&lt;History&gt;", html)
            self.assertIn("&lt;api&gt;", html)
            self.assertNotIn("<h1><History>", html)


if __name__ == "__main__":
    unittest.main()
