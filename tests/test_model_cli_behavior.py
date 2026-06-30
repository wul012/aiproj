from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

from scripts import chat, eval_suite, evaluate, generate, inspect_attention, inspect_predictions, train
from tests.model_cli_fixtures import make_tiny_checkpoint

ensure_src_path()


class ModelCliBehaviorTests(unittest.TestCase):
    def test_tiny_checkpoint_foundation_mains_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint_path, tokenizer_path, data_path, suite_path = make_tiny_checkpoint(root)

            eval_report_path = root / "eval_report.json"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                evaluate_exit_code = evaluate.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--data",
                        str(data_path),
                        "--split",
                        "val",
                        "--train-ratio",
                        "0.5",
                        "--eval-iters",
                        "1",
                        "--batch-size",
                        "2",
                        "--out",
                        str(eval_report_path),
                        "--device",
                        "cpu",
                    ]
                )

            self.assertEqual(evaluate_exit_code, 0)
            self.assertIn(f"saved={eval_report_path}", stdout.getvalue())
            eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
            self.assertEqual(eval_report["tokenizer"], "char")
            self.assertEqual(eval_report["eval_iters"], 1)

            eval_suite_out = root / "eval-suite"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                eval_suite_exit_code = eval_suite.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--suite",
                        str(suite_path),
                        "--out-dir",
                        str(eval_suite_out),
                        "--device",
                        "cpu",
                    ]
                )

            eval_suite_output = stdout.getvalue()
            self.assertEqual(eval_suite_exit_code, 0)
            self.assertIn("cases=1", eval_suite_output)
            self.assertIn("suite_name=tiny-suite", eval_suite_output)
            self.assertTrue((eval_suite_out / "eval_suite.json").is_file())
            self.assertTrue((eval_suite_out / "eval_suite.html").is_file())

            generated_path = root / "generated.txt"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                generate_exit_code = generate.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--prompt",
                        "abc",
                        "--max-new-tokens",
                        "2",
                        "--top-k",
                        "5",
                        "--seed",
                        "1",
                        "--device",
                        "cpu",
                        "--out",
                        str(generated_path),
                    ]
                )

            self.assertEqual(generate_exit_code, 0)
            self.assertIn(f"saved={generated_path}", stdout.getvalue())
            self.assertTrue(generated_path.read_text(encoding="utf-8"))

            predictions_out = root / "predictions"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                predictions_exit_code = inspect_predictions.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--prompt",
                        "abc",
                        "--top-k",
                        "3",
                        "--out-dir",
                        str(predictions_out),
                        "--device",
                        "cpu",
                    ]
                )

            predictions_output = stdout.getvalue()
            self.assertEqual(predictions_exit_code, 0)
            self.assertIn("tokenizer=char", predictions_output)
            self.assertIn("saved_json=", predictions_output)
            predictions = json.loads((predictions_out / "predictions.json").read_text(encoding="utf-8"))
            self.assertEqual(len(predictions["predictions"]), 3)
            self.assertTrue((predictions_out / "predictions.svg").is_file())

            attention_out = root / "attention"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                attention_exit_code = inspect_attention.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--prompt",
                        "abc",
                        "--layer",
                        "0",
                        "--head",
                        "0",
                        "--out-dir",
                        str(attention_out),
                        "--device",
                        "cpu",
                    ]
                )

            attention_output = stdout.getvalue()
            self.assertEqual(attention_exit_code, 0)
            self.assertIn("tokenizer=char", attention_output)
            self.assertIn("last_token_top_links=", attention_output)
            attention = json.loads((attention_out / "attention.json").read_text(encoding="utf-8"))
            self.assertEqual(attention["tokens"], ["a", "b", "c"])
            self.assertTrue((attention_out / "attention.svg").is_file())

    def test_chat_and_tiny_train_mains_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint_path, tokenizer_path, _data_path, _suite_path = make_tiny_checkpoint(root)
            transcript_path = root / "chat.json"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                chat_exit_code = chat.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--message",
                        "abc",
                        "--max-new-tokens",
                        "2",
                        "--top-k",
                        "5",
                        "--device",
                        "cpu",
                        "--out",
                        str(transcript_path),
                    ]
                )

            chat_output = stdout.getvalue()
            self.assertEqual(chat_exit_code, 0)
            self.assertIn("tokenizer=char", chat_output)
            self.assertIn("context_tokens=", chat_output)
            self.assertIn(f"saved={transcript_path}", chat_output)
            transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
            self.assertEqual(transcript["tokenizer"], "char")
            self.assertEqual(transcript["turns"][0]["role"], "user")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_path = root / "train.txt"
            data_path.write_text("abcdefghijklmnopqrstuvwx " * 4, encoding="utf-8")
            out_dir = root / "run"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                train_exit_code = train.main(
                    [
                        "--data",
                        str(data_path),
                        "--out-dir",
                        str(out_dir),
                        "--tokenizer",
                        "char",
                        "--batch-size",
                        "2",
                        "--block-size",
                        "8",
                        "--max-iters",
                        "1",
                        "--eval-interval",
                        "1",
                        "--eval-iters",
                        "1",
                        "--learning-rate",
                        "0.001",
                        "--train-ratio",
                        "0.8",
                        "--n-layer",
                        "1",
                        "--n-head",
                        "2",
                        "--n-embd",
                        "8",
                        "--dropout",
                        "0.0",
                        "--seed",
                        "1",
                        "--device",
                        "cpu",
                        "--no-sample",
                    ]
                )

            train_output = stdout.getvalue()
            self.assertEqual(train_exit_code, 0)
            self.assertIn("device=cpu", train_output)
            self.assertIn("tokenizer=char", train_output)
            self.assertIn(f"saved={out_dir}", train_output)
            self.assertTrue((out_dir / "checkpoint.pt").is_file())
            self.assertTrue((out_dir / "tokenizer.json").is_file())
            self.assertTrue((out_dir / "train_config.json").is_file())
            self.assertTrue((out_dir / "metrics.jsonl").is_file())
            manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["training"]["end_step"], 1)


if __name__ == "__main__":
    unittest.main()
