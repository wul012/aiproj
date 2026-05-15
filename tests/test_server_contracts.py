from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server
from minigpt import server_contracts


class ServerContractsSplitTests(unittest.TestCase):
    def test_contract_module_builds_checkpoint_payloads_without_handler(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"default")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            candidate = run_dir / "candidate" / "checkpoint.pt"
            candidate.parent.mkdir()
            candidate.write_bytes(b"candidate")
            (candidate.parent / "tokenizer.json").write_text("{}", encoding="utf-8")
            (candidate.parent / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "training": {"tokenizer": "char"},
                        "model": {"parameter_count": 7, "config": {"n_layer": 1}},
                        "data": {"dataset_version": {"id": "demo@v1", "short_fingerprint": "abc123"}},
                    }
                ),
                encoding="utf-8",
            )

            health = server_contracts.build_health_payload(run_dir)
            checkpoints = server_contracts.build_checkpoints_payload(run_dir)
            compare = server_contracts.build_checkpoint_compare_payload(run_dir)

            self.assertEqual(health["default_checkpoint_id"], "default")
            self.assertEqual(checkpoints["checkpoint_count"], 2)
            rows = {row["id"]: row for row in compare["checkpoints"]}
            self.assertEqual(rows["candidate"]["parameter_count"], 7)
            self.assertEqual(rows["candidate"]["dataset_version"], "demo@v1")

    def test_contract_module_builds_request_and_pair_payloads(self) -> None:
        request = server_contracts.parse_generation_request(
            {"prompt": "hello", "max_new_tokens": "3", "temperature": "0.7", "top_k": "0", "seed": "9"}
        )
        pair_request = server_contracts.parse_generation_pair_request(
            {
                "prompt": "hello",
                "max_new_tokens": 3,
                "left_checkpoint": "default",
                "right_checkpoint": "candidate",
            }
        )
        left_option = server_contracts.CheckpointOption("default", "default", "left.pt", True, True, None, False, "default")
        right_option = server_contracts.CheckpointOption("candidate", "candidate", "right.pt", True, False, None, False, "candidate")
        left_response = server_contracts.GenerationResponse("hello", "hello A", " A", 3, 0.8, 30, None, "left.pt", "char")
        right_response = server_contracts.GenerationResponse("hello", "hello BB", " BB", 3, 0.8, 30, None, "right.pt", "char")

        timeout = server_contracts.stream_timeout_payload(
            request,
            elapsed_seconds=1.2345678,
            max_stream_seconds=1.0,
            chunk_count=2,
            generated="hello A",
            continuation=" A",
            checkpoint="left.pt",
            tokenizer="char",
            checkpoint_id="default",
        )
        payload = server_contracts.pair_generation_payload(pair_request, left_option, right_option, left_response, right_response)

        self.assertEqual(request.seed, 9)
        self.assertIsNone(request.top_k)
        self.assertEqual(timeout["elapsed_seconds"], 1.234568)
        self.assertEqual(payload["right"]["checkpoint_id"], "candidate")
        self.assertEqual(payload["comparison"]["generated_char_delta"], 1)

    def test_server_facade_keeps_legacy_contract_exports(self) -> None:
        self.assertIs(server.InferenceSafetyProfile, server_contracts.InferenceSafetyProfile)
        self.assertIs(server.CheckpointOption, server_contracts.CheckpointOption)
        self.assertIs(server.GenerationRequest, server_contracts.GenerationRequest)
        self.assertIs(server.GenerationResponse, server_contracts.GenerationResponse)
        self.assertIs(server.parse_generation_request, server_contracts.parse_generation_request)
        self.assertIs(server.parse_generation_pair_request, server_contracts.parse_generation_pair_request)
        self.assertIs(server.build_health_payload, server_contracts.build_health_payload)
        self.assertIs(server.build_model_info_payload, server_contracts.build_model_info_payload)
        self.assertIs(server.build_checkpoint_compare_payload, server_contracts.build_checkpoint_compare_payload)
        self.assertIs(server.discover_checkpoint_options, server_contracts.discover_checkpoint_options)
        self.assertIs(server.sse_message, server_contracts.sse_message)
        self.assertIs(server.stream_timeout_payload, server_contracts.stream_timeout_payload)


if __name__ == "__main__":
    unittest.main()
