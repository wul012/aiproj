from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.tokenizer import BPETokenizer, CharTokenizer, load_tokenizer


class CharTokenizerTests(unittest.TestCase):
    def test_round_trip_known_text(self) -> None:
        tokenizer = CharTokenizer.train("人工智能\n模型")

        ids = tokenizer.encode("人工智能")

        self.assertEqual(tokenizer.decode(ids), "人工智能")
        self.assertGreaterEqual(tokenizer.vocab_size, 6)

    def test_unknown_character_uses_unknown_token(self) -> None:
        tokenizer = CharTokenizer.train("abc")

        ids = tokenizer.encode("az")

        self.assertEqual(ids[0], tokenizer.stoi["a"])
        self.assertEqual(ids[1], tokenizer.stoi[tokenizer.unk_token])
        self.assertEqual(tokenizer.decode(ids), "a�")

    def test_char_save_and_auto_load(self) -> None:
        import tempfile

        tokenizer = CharTokenizer.train("人工智能")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokenizer.json"
            tokenizer.save(path)

            loaded = load_tokenizer(path)

            self.assertIsInstance(loaded, CharTokenizer)
            self.assertEqual(loaded.decode(loaded.encode("人工智能")), "人工智能")

    def test_old_char_payload_auto_loads_without_type(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokenizer.json"
            path.write_text('{"itos": ["<unk>", "a", "b"], "unk_token": "<unk>"}', encoding="utf-8")

            loaded = load_tokenizer(path)

            self.assertIsInstance(loaded, CharTokenizer)
            self.assertEqual(loaded.decode(loaded.encode("ab")), "ab")

class BPETokenizerTests(unittest.TestCase):
    def test_bpe_learns_repeated_pair(self) -> None:
        tokenizer = BPETokenizer.train("abababab", vocab_size=8, min_frequency=2)

        ids = tokenizer.encode("abab")

        self.assertIn(("a", "b"), tokenizer.merges)
        self.assertLess(len(ids), 4)
        self.assertEqual(tokenizer.decode(ids), "abab")

    def test_bpe_save_and_load(self) -> None:
        import tempfile

        tokenizer = BPETokenizer.train("人工智能人工智能", vocab_size=16, min_frequency=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokenizer.json"
            tokenizer.save(path)

            loaded = load_tokenizer(path)

            self.assertIsInstance(loaded, BPETokenizer)
            self.assertEqual(loaded.decode(loaded.encode("人工智能")), "人工智能")


if __name__ == "__main__":
    unittest.main()
