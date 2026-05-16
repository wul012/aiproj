from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server
from minigpt import server_checkpoints
from minigpt import server_contracts
from minigpt.server_contracts import InferenceSafetyProfile


class ServerCheckpointsSplitTests(unittest.TestCase):
    def test_checkpoint_module_builds_health_model_info_and_compare_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"default")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            candidate = run_dir / "candidate" / "checkpoint.pt"
            candidate.parent.mkdir()
            candidate.write_bytes(b"candidate-model")
            (candidate.parent / "tokenizer.json").write_text("{}", encoding="utf-8")
            (candidate.parent / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "training": {"tokenizer": "char"},
                        "model": {"parameter_count": 13, "config": {"n_layer": 2}},
                        "data": {"dataset_version": {"id": "demo@v2", "short_fingerprint": "def456"}},
                        "artifacts": [{"exists": True}, {"exists": False}],
                    }
                ),
                encoding="utf-8",
            )

            health = server_checkpoints.build_health_payload(run_dir, safety_profile=InferenceSafetyProfile(max_new_tokens=9))
            checkpoints = server_checkpoints.build_checkpoints_payload(run_dir)
            compare = server_checkpoints.build_checkpoint_compare_payload(run_dir)
            candidate_option = next(option for option in server_checkpoints.discover_checkpoint_options(run_dir) if option.id == "candidate")
            info = server_checkpoints.build_model_info_payload(
                server_checkpoints.metadata_run_dir(run_dir, candidate_option),
                candidate_option.path,
                candidate_option.tokenizer_path,
                candidate_option.id,
            )

            self.assertEqual(health["default_checkpoint_id"], "default")
            self.assertEqual(health["safety"]["max_new_tokens"], 9)
            self.assertEqual(checkpoints["checkpoint_count"], 2)
            rows = {row["id"]: row for row in compare["checkpoints"]}
            self.assertEqual(rows["candidate"]["parameter_count"], 13)
            self.assertEqual(rows["candidate"]["dataset_version"], "demo@v2")
            self.assertEqual(info["artifact_count"], 1)

    def test_contracts_and_server_keep_legacy_checkpoint_exports(self) -> None:
        self.assertIs(server_contracts.CheckpointOption, server_checkpoints.CheckpointOption)
        self.assertIs(server_contracts.build_model_info_payload, server_checkpoints.build_model_info_payload)
        self.assertIs(server_contracts.build_checkpoint_compare_payload, server_checkpoints.build_checkpoint_compare_payload)
        self.assertIs(server_contracts.discover_checkpoint_options, server_checkpoints.discover_checkpoint_options)
        self.assertIs(server_contracts.resolve_checkpoint_option, server_checkpoints.resolve_checkpoint_option)
        self.assertIs(server_contracts.metadata_run_dir, server_checkpoints.metadata_run_dir)
        self.assertIs(server.CheckpointOption, server_checkpoints.CheckpointOption)
        self.assertIs(server.build_model_info_payload, server_checkpoints.build_model_info_payload)
        self.assertIs(server.build_checkpoint_compare_payload, server_checkpoints.build_checkpoint_compare_payload)
        self.assertIs(server.discover_checkpoint_options, server_checkpoints.discover_checkpoint_options)


if __name__ == "__main__":
    unittest.main()
