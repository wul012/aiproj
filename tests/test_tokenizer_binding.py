from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from minigpt.training.tokenizer_binding import tokenizer_digest, validate_tokenizer_binding
from minigpt.core.tokenizer import BPETokenizer, CharTokenizer, load_tokenizer
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint, tiny_resume_args

ensure_src_path()


class TokenizerResumeTests(unittest.TestCase):
    def test_digest_ignores_json_presentation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokenizer.json"
            tokenizer = CharTokenizer.train("abca")
            tokenizer.save(path)
            loaded = load_tokenizer(path)
            path.write_text(json.dumps(json.loads(path.read_text()), sort_keys=True), encoding="utf-8")
            reformatted = load_tokenizer(path)
            self.assertEqual(tokenizer_digest(tokenizer), tokenizer_digest(loaded))
            self.assertEqual(tokenizer_digest(loaded), tokenizer_digest(reformatted))
            validate_tokenizer_binding({"tokenizer_sha256": tokenizer_digest(tokenizer)}, reformatted)

    def test_bpe_merge_order_is_bound(self) -> None:
        tokenizer = BPETokenizer.train("abababab " * 20, vocab_size=12, min_frequency=2)
        self.assertTrue(tokenizer.merges)
        digest = tokenizer_digest(tokenizer)
        changed = BPETokenizer(tokenizer.stoi, tokenizer.itos, list(reversed(tokenizer.merges)))
        self.assertNotEqual(digest, tokenizer_digest(changed))
        with self.assertRaisesRegex(ValueError, "tokenizer.*mismatch"):
            validate_tokenizer_binding({"tokenizer_sha256": digest}, changed)

    def test_same_size_swap_rejected_early(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "run"
            run.mkdir()
            checkpoint, tokenizer, data, _ = make_tiny_checkpoint(run)
            args = tiny_resume_args(checkpoint, data, 2)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(train.main(args), 0)
            payload = json.loads(tokenizer.read_text(encoding="utf-8"))
            payload["itos"][1], payload["itos"][2] = payload["itos"][2], payload["itos"][1]
            tokenizer.write_text(json.dumps(payload), encoding="utf-8")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "tokenizer.*mismatch"):
                    train.main(args + ["--max-iters", "3", "--out-dir", str(root / "new-run")])
            self.assertFalse((root / "new-run").exists())
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
