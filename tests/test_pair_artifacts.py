from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.pair_artifacts import (  # noqa: E402
    artifact_href,
    render_pair_generation_html,
    slug,
    timestamp_slug,
    unique_pair_artifact_stem,
    write_pair_generation_artifacts,
)
from minigpt.server import render_pair_generation_html as server_render_pair_generation_html  # noqa: E402
from minigpt.server import write_pair_generation_artifacts as server_write_pair_generation_artifacts  # noqa: E402


def sample_payload() -> dict:
    return {
        "prompt": "abc <prompt>",
        "max_new_tokens": 5,
        "temperature": 0.8,
        "top_k": None,
        "seed": 7,
        "left": {"checkpoint_id": "Default/One", "generated": "left <generated>", "continuation": "left"},
        "right": {"checkpoint_id": "Wide Two", "generated": "right > generated", "continuation": "right"},
        "comparison": {
            "generated_equal": False,
            "generated_char_delta": 2,
            "continuation_equal": False,
            "continuation_char_delta": 1,
        },
    }


class PairArtifactsTests(unittest.TestCase):
    def test_slug_and_timestamp_slug_are_stable(self) -> None:
        self.assertEqual(slug("Default/One"), "default-one")
        self.assertEqual(slug("Wide Two!"), "wide-two")
        self.assertEqual(slug(""), "checkpoint")
        self.assertEqual(timestamp_slug("2026-05-15T01:02:03Z"), "2026-05-15t01-02-03utc")

    def test_unique_pair_artifact_stem_avoids_json_and_html_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pair.json").write_text("{}", encoding="utf-8")
            self.assertEqual(unique_pair_artifact_stem(root, "pair"), "pair-2")
            (root / "pair-2.html").write_text("<html></html>", encoding="utf-8")
            self.assertEqual(unique_pair_artifact_stem(root, "pair"), "pair-3")

    def test_artifact_href_prefers_run_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "pair_generations" / "demo.html"
            nested.parent.mkdir()
            nested.write_text("<html></html>", encoding="utf-8")

            self.assertEqual(artifact_href(root, nested), "pair_generations/demo.html")
            self.assertTrue(artifact_href(root, Path(tmp).parent / "outside.html").endswith("outside.html"))

    def test_write_pair_generation_artifacts_writes_json_and_escaped_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            artifact = write_pair_generation_artifacts(root, sample_payload(), created_at="2026-05-15T01:02:03Z")

            json_path = Path(artifact["json_path"])
            html_path = Path(artifact["html_path"])
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())
            self.assertEqual(json_path.name, "2026-05-15t01-02-03utc-default-one-vs-wide-two.json")
            self.assertEqual(artifact["json_href"], "pair_generations/2026-05-15t01-02-03utc-default-one-vs-wide-two.json")
            record = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(record["kind"], "minigpt_pair_generation")
            self.assertEqual(record["left"]["checkpoint_id"], "Default/One")
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("MiniGPT Pair Generation", html)
            self.assertIn("left &lt;generated&gt;", html)
            self.assertNotIn("left <generated>", html)

    def test_server_wrappers_delegate_to_pair_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            direct = write_pair_generation_artifacts(root / "direct", sample_payload(), created_at="2026-05-15T01:02:03Z")
            wrapped = server_write_pair_generation_artifacts(root / "wrapped", sample_payload(), created_at="2026-05-15T01:02:03Z")

            self.assertTrue(Path(direct["json_path"]).exists())
            self.assertTrue(Path(wrapped["json_path"]).exists())
            record = json.loads(Path(wrapped["json_path"]).read_text(encoding="utf-8"))
            self.assertEqual(server_render_pair_generation_html(record), render_pair_generation_html(record))


if __name__ == "__main__":
    unittest.main()
