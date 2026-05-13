from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.playground import build_playground_commands, build_playground_payload, render_playground_html, write_playground


class PlaygroundTests(unittest.TestCase):
    def test_build_payload_reads_sampling_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": "char"}), encoding="utf-8")
            (run_dir / "run_manifest.json").write_text(json.dumps({"git": {"short_commit": "abc1234"}}), encoding="utf-8")
            (run_dir / "dataset_quality.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            (run_dir / "dataset_version.html").write_text("<html></html>", encoding="utf-8")
            (run_dir / "experiment_card.html").write_text("<html></html>", encoding="utf-8")
            eval_suite_dir = run_dir / "eval_suite"
            eval_suite_dir.mkdir()
            (eval_suite_dir / "eval_suite.json").write_text(json.dumps({"case_count": 1, "results": []}), encoding="utf-8")
            sample_dir = run_dir / "sample_lab"
            sample_dir.mkdir()
            (sample_dir / "sample_lab.json").write_text(
                json.dumps(
                    {
                        "prompt": "abc",
                        "results": [
                            {
                                "name": "balanced",
                                "temperature": 0.8,
                                "top_k": 30,
                                "seed": 1,
                                "continuation": "def",
                                "unique_char_count": 3,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_playground_payload(run_dir)

            self.assertEqual(payload["summary"]["tokenizer"], "char")
            self.assertEqual(payload["summary"]["sampling_cases"], 1)
            self.assertTrue(any(link["key"] == "sample_lab_json" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "run_manifest" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "dataset_quality" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "dataset_version_html" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "eval_suite" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "experiment_card_html" and link["exists"] for link in payload["links"]))

    def test_playground_links_pair_batch_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            pair_batch_dir = run_dir / "pair_batch"
            pair_batch_dir.mkdir()
            (pair_batch_dir / "pair_generation_batch.html").write_text("<html></html>", encoding="utf-8")
            pair_trend_dir = run_dir / "pair_batch_trend"
            pair_trend_dir.mkdir()
            (pair_trend_dir / "pair_batch_trend.html").write_text("<html></html>", encoding="utf-8")

            payload = build_playground_payload(run_dir)
            html = render_playground_html(payload)

            self.assertTrue(any(link["key"] == "pair_batch_html" and link["exists"] for link in payload["links"]))
            self.assertTrue(any(link["key"] == "pair_trend_html" and link["exists"] for link in payload["links"]))
            self.assertIn("Pair batch HTML", html)
            self.assertIn("pair_batch/pair_generation_batch.html", html)
            self.assertIn("Pair trend HTML", html)
            self.assertIn("pair_batch_trend/pair_batch_trend.html", html)

    def test_render_playground_escapes_text_and_has_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "sample.txt").write_text("<script>alert(1)</script>", encoding="utf-8")

            payload = build_playground_payload(run_dir, title="<MiniGPT>")
            html = render_playground_html(payload)

            self.assertIn("&lt;MiniGPT&gt;", html)
            self.assertIn('id="promptInput"', html)
            self.assertIn("generateCommand", html)
            self.assertIn("liveGenerateButton", html)
            self.assertIn("liveStopButton", html)
            self.assertIn("Stream Generate", html)
            self.assertIn("Stop", html)
            self.assertIn("AbortController", html)
            self.assertIn("stopLiveGeneration", html)
            self.assertIn("MiniGPTPlayground.streamController === controller", html)
            self.assertIn("checkpointSelect", html)
            self.assertIn("/api/checkpoints", html)
            self.assertIn("/api/generate-stream", html)
            self.assertIn("readGenerationStream", html)
            self.assertIn("stream timeout", html)
            self.assertIn("checkpointCompareTable", html)
            self.assertIn("/api/checkpoint-compare", html)
            self.assertIn("selectCheckpoint", html)
            self.assertIn("pairLeftCheckpointSelect", html)
            self.assertIn("pairRightCheckpointSelect", html)
            self.assertIn("pairGenerateButton", html)
            self.assertIn("pairSaveButton", html)
            self.assertIn("pairArtifactStatus", html)
            self.assertIn("/api/generate-pair", html)
            self.assertIn("/api/generate-pair-artifact", html)
            self.assertIn("left_checkpoint", html)
            self.assertIn("right_checkpoint", html)
            self.assertIn("payload.checkpoint", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_build_playground_commands_quote_paths_and_prompt(self) -> None:
        run_dir = Path("runs/minigpt")
        commands = build_playground_commands(run_dir, prompt='hello "ai"')

        self.assertIn(f"'{run_dir / 'checkpoint.pt'}'", commands["generate"])
        self.assertIn("'hello \"ai\"'", commands["generate"])
        self.assertIn("sample_lab.py", commands["sample_lab"])
        self.assertIn("pair_batch.py", commands["pair_batch"])
        self.assertIn("compare_pair_batches.py", commands["pair_trend"])
        self.assertIn("build_experiment_card.py", commands["experiment_card"])

    def test_write_playground_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            out_path = run_dir / "playground.html"

            payload = write_playground(run_dir, output_path=out_path)

            self.assertTrue(out_path.exists())
            self.assertIn("MiniGPT playground", out_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["output_path"], str(out_path))
            self.assertTrue(next(link for link in payload["links"] if link["key"] == "playground")["exists"])


if __name__ == "__main__":
    unittest.main()
