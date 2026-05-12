from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.manifest import build_run_manifest, collect_run_artifacts, sha256_file, write_run_manifest_json, write_run_manifest_svg


class ManifestTests(unittest.TestCase):
    def test_sha256_file_hashes_small_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("abc", encoding="utf-8")

            digest = sha256_file(path)

            self.assertEqual(digest, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_collect_run_artifacts_marks_manifest_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"model")
            (run_dir / "metrics.jsonl").write_text("{}", encoding="utf-8")
            (run_dir / "experiment_card.md").write_text("# card", encoding="utf-8")

            artifacts = collect_run_artifacts(run_dir)

            checkpoint = next(item for item in artifacts if item["key"] == "checkpoint")
            self.assertTrue(checkpoint["exists"])
            self.assertEqual(checkpoint["path"], "checkpoint.pt")
            self.assertIsNotNone(checkpoint["sha256"])
            card = next(item for item in artifacts if item["key"] == "experiment_card_md")
            self.assertTrue(card["exists"])

    def test_build_run_manifest_records_reproducibility_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            (run_dir / "dataset_report.json").write_text(
                json.dumps({"source_count": 2, "char_count": 120, "line_count": 4, "unique_char_count": 30}),
                encoding="utf-8",
            )
            (run_dir / "dataset_quality.json").write_text(
                json.dumps({"status": "pass", "fingerprint": "a" * 64, "short_fingerprint": "a" * 12, "issue_count": 0, "warning_count": 0}),
                encoding="utf-8",
            )

            manifest = build_run_manifest(
                run_dir,
                args={"max_iters": 2, "data": Path("data/sample.txt")},
                data_source={"kind": "data", "path": "data/sample.txt"},
                model_config={"block_size": 8, "n_layer": 1},
                tokenizer_name="char",
                token_count=100,
                train_token_count=90,
                val_token_count=10,
                parameter_count=1234,
                device_used="cpu",
                started_at="2026-05-12T00:00:00Z",
                finished_at="2026-05-12T00:00:03Z",
                start_step=1,
                end_step=2,
                last_loss=1.23,
                history_summary={"best_val_loss": 1.1},
                command=["python", "scripts/train.py"],
                repo_root=tmp,
                environment={"python": "test"},
            )

            self.assertEqual(manifest["duration_seconds"], 3.0)
            self.assertEqual(manifest["data"]["dataset_report"]["source_count"], 2)
            self.assertEqual(manifest["data"]["dataset_quality"]["status"], "pass")
            self.assertEqual(manifest["training"]["args"]["data"], str(Path("data/sample.txt")))
            self.assertEqual(manifest["results"]["history_summary"]["best_val_loss"], 1.1)

    def test_write_run_manifest_outputs_json_and_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = {
                "run_dir": "run",
                "duration_seconds": 1.0,
                "git": {"short_commit": "abc1234", "dirty": False},
                "data": {"token_count": 10},
                "model": {"parameter_count": 20},
                "results": {"history_summary": {"best_val_loss": 1.0}},
                "artifacts": [{"key": "checkpoint", "exists": True, "size_bytes": 4}],
            }
            root = Path(tmp)

            write_run_manifest_json(manifest, root / "run_manifest.json")
            write_run_manifest_svg(manifest, root / "run_manifest.svg")

            self.assertEqual(json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))["run_dir"], "run")
            self.assertIn("<svg", (root / "run_manifest.svg").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
