from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server
from minigpt import server_logging
from minigpt.server_contracts import (
    CheckpointOption,
    GenerationPairRequest,
    GenerationRequest,
    GenerationResponse,
)


class ServerLoggingSplitTests(unittest.TestCase):
    def test_generation_log_event_records_request_response_and_stream_fields(self) -> None:
        request = GenerationRequest("hello", 5, 0.7, None, 42, "candidate")
        response = GenerationResponse("hello", "hello world", " world", 5, 0.7, None, 42, "candidate.pt", "char", "candidate")
        option = CheckpointOption("candidate", "Candidate", "candidate.pt", True, False, "tokenizer.json", True, "candidate")

        event = server_logging.build_generation_log_event(
            "ok",
            endpoint="/api/generate-stream",
            client="127.0.0.1",
            default_checkpoint="default.pt",
            request=request,
            response=response,
            checkpoint_option=option,
            stream_chunks=3,
            stream_timed_out=False,
            stream_cancelled=False,
            stream_elapsed_seconds=0.1234567,
        )

        self.assertEqual(event["endpoint"], "/api/generate-stream")
        self.assertEqual(event["checkpoint_id"], "candidate")
        self.assertEqual(event["requested_checkpoint"], "candidate")
        self.assertEqual(event["generated_chars"], len("hello world"))
        self.assertEqual(event["continuation_chars"], len(" world"))
        self.assertEqual(event["stream_chunks"], 3)
        self.assertEqual(event["stream_elapsed_seconds"], 0.123457)

    def test_generation_log_event_uses_default_checkpoint_without_option(self) -> None:
        event = server_logging.build_generation_log_event(
            "bad_request",
            client="127.0.0.1",
            default_checkpoint="runs/default/checkpoint.pt",
            error="prompt cannot be empty",
        )

        self.assertEqual(event["checkpoint"], "runs/default/checkpoint.pt")
        self.assertIsNone(event["checkpoint_id"])
        self.assertEqual(event["error"], "prompt cannot be empty")

    def test_pair_generation_log_event_records_comparison_and_artifact_paths(self) -> None:
        left_request = GenerationRequest("hello", 4, 0.8, 30, 9, "left")
        right_request = GenerationRequest("hello", 4, 0.8, 30, 9, "right")
        pair_request = GenerationPairRequest(left_request, right_request)
        left_option = CheckpointOption("left", "Left", "left.pt", True, False, None, False, "candidate")
        right_option = CheckpointOption("right", "Right", "right.pt", True, False, None, False, "candidate")
        left_response = GenerationResponse("hello", "hello A", " A", 4, 0.8, 30, 9, "left.pt", "char", "left")
        right_response = GenerationResponse("hello", "hello BB", " BB", 4, 0.8, 30, 9, "right.pt", "char", "right")

        event = server_logging.build_pair_generation_log_event(
            "ok",
            endpoint="/api/generate-pair-artifact",
            client="127.0.0.1",
            pair_request=pair_request,
            left_option=left_option,
            right_option=right_option,
            left_response=left_response,
            right_response=right_response,
            artifact={"json_path": "pairs/item.json", "html_path": "pairs/item.html"},
        )

        self.assertEqual(event["endpoint"], "/api/generate-pair-artifact")
        self.assertEqual(event["left_checkpoint_id"], "left")
        self.assertEqual(event["right_checkpoint_id"], "right")
        self.assertFalse(event["generated_equal"])
        self.assertFalse(event["continuation_equal"])
        self.assertEqual(event["artifact_json"], "pairs/item.json")
        self.assertEqual(event["artifact_html"], "pairs/item.html")

    def test_server_facade_keeps_legacy_logging_exports(self) -> None:
        self.assertIs(server.build_generation_log_event, server_logging.build_generation_log_event)
        self.assertIs(server.build_pair_generation_log_event, server_logging.build_pair_generation_log_event)


if __name__ == "__main__":
    unittest.main()
