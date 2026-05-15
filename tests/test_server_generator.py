from __future__ import annotations

import sys
import unittest
from pathlib import Path
from inspect import signature

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server  # noqa: E402
from minigpt.server_generator import MiniGPTGenerator  # noqa: E402


class ServerGeneratorSplitTests(unittest.TestCase):
    def test_server_module_reexports_generator_class(self) -> None:
        self.assertIs(server.MiniGPTGenerator, MiniGPTGenerator)
        self.assertIs(signature(server.create_handler).parameters["generator_factory"].default, MiniGPTGenerator)

    def test_generator_defaults_tokenizer_next_to_checkpoint(self) -> None:
        generator = MiniGPTGenerator("runs/demo/checkpoint.pt", device="cpu")

        self.assertEqual(generator.checkpoint_path, Path("runs/demo/checkpoint.pt"))
        self.assertEqual(generator.tokenizer_path, Path("runs/demo/tokenizer.json"))
        self.assertEqual(generator.device_name, "cpu")
        self.assertIsNone(generator._loaded)

    def test_generator_accepts_explicit_tokenizer_path(self) -> None:
        generator = MiniGPTGenerator("runs/demo/checkpoint.pt", "artifacts/tokenizer.json", "auto")

        self.assertEqual(generator.tokenizer_path, Path("artifacts/tokenizer.json"))
        self.assertEqual(generator.device_name, "auto")


if __name__ == "__main__":
    unittest.main()
