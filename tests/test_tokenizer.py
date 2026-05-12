from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.tokenizer import CharTokenizer


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


if __name__ == "__main__":
    unittest.main()
