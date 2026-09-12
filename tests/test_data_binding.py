from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.data_binding import build_data_binding, validate_data_binding
from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint, tiny_resume_args

ensure_src_path()


def inventory(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class DataBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, self.threads)

    def fresh_args(self, data: Path, out: Path, ratio: str = "0.5") -> list[str]:
        return [
            "--data",
            str(data),
            "--out-dir",
            str(out),
            "--device",
            "cpu",
            "--batch-size",
            "2",
            "--block-size",
            "8",
            "--n-layer",
            "1",
            "--n-head",
            "2",
            "--n-embd",
            "8",
            "--dropout",
            "0.0",
            "--max-iters",
            "2",
            "--eval-interval",
            "1",
            "--eval-iters",
            "1",
            "--train-ratio",
            ratio,
            "--no-sample",
        ]

    def test_text_drift_preserves_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdef " * 20, encoding="utf-8")
            out = root / "run"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(train.main(self.fresh_args(data, out)), 0)
            data.write_text("abcdef " * 20 + "a", encoding="utf-8")
            (out / "metrics.jsonl").write_bytes((out / "metrics.jsonl").read_bytes() + b"suffix")
            before = inventory(root)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "data binding"):
                train.main(tiny_resume_args(out / "checkpoint.pt", data, 3))
            self.assertEqual(inventory(root), before)

    def test_ratio_drift_and_path_move(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("abcdef " * 20, encoding="utf-8")
            out = root / "run"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(train.main(self.fresh_args(data, out)), 0)
            alternate = root / "alternate.txt"
            alternate.write_bytes(data.read_bytes())
            with (out / "metrics.jsonl").open("ab") as stream:
                stream.write(b"uncommitted suffix")
            before = inventory(root)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "data binding"):
                train.main(tiny_resume_args(out / "checkpoint.pt", data, 3) + ["--train-ratio", "0.6"])
            self.assertEqual(inventory(root), before)
            branch = root / "branch"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    train.main(tiny_resume_args(out / "checkpoint.pt", alternate, 3) + ["--out-dir", str(branch)]),
                    0,
                )
            self.assertEqual(
                inventory(out),
                {str(Path(k).relative_to("run")): v for k, v in before.items() if Path(k).parts[0] == "run"},
            )

    def test_legacy_without_binding_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
            saved.pop("data_binding", None)
            torch.save(saved, checkpoint)
            data.write_text(data.read_text(encoding="utf-8") + "a", encoding="utf-8")
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 3)), 0)
            self.assertEqual(torch.load(checkpoint, map_location="cpu", weights_only=False)["step"], 3)

    def test_binding_payload_is_versioned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            binding = torch.load(checkpoint, map_location="cpu", weights_only=False)["data_binding"]
            self.assertEqual(binding["version"], 1)
            self.assertEqual(binding["text_length"], len(data.read_text(encoding="utf-8")))
            self.assertEqual(binding["train_ratio"], 0.5)
            self.assertEqual(len(binding["text_sha256"]), 64)

    def test_invalid_binding_is_not_legacy(self) -> None:
        current = build_data_binding("数据abc", 0.5)
        cases = [None, [], {}, "bad", current | {"version": True}, current | {"version": 1.0}]
        cases += [{k: v for k, v in current.items() if k != field} for field in current]
        cases += [current | {"text_length": value} for value in (True, 5.0, -1)]
        cases += [current | {"train_ratio": value} for value in (True, "0.5", float("nan"), float("inf"), 0, 1)]
        cases += [current | {"text_sha256": value} for value in (None, "bad")]
        cases.append(current | {"unexpected": 1})
        for index, binding in enumerate(cases):
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "data binding"):
                validate_data_binding({"data_binding": binding}, "数据abc", 0.5)
        self.assertIsNone(validate_data_binding({}, "different", 0.6))
        self.assertIsNone(validate_data_binding({"data_binding": current}, "数据abc", 0.5))
        self.assertEqual(current, build_data_binding("数据abc", 0.5))

    def test_same_length_drift_before_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            text = data.read_text(encoding="utf-8")
            data.write_text(text.replace("ab", "ba", 1), encoding="utf-8")
            before = inventory(root)
            with patch.object(train, "MiniGPT") as model, self.assertRaisesRegex(ValueError, "data binding"):
                train.main(tiny_resume_args(checkpoint, data, 3) + ["--out-dir", str(root / "new")])
            model.assert_not_called()
            self.assertFalse((root / "new").exists())
            self.assertEqual(inventory(root), before)

    def test_loaded_text_not_raw_file_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            data.write_bytes(("abcdef \r\n" * 20).encode())
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            before = torch.load(checkpoint, map_location="cpu", weights_only=False)["data_binding"]
            data.write_bytes(data.read_bytes().replace(b"\r\n", b"\n"))
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 3)), 0)
            after = torch.load(checkpoint, map_location="cpu", weights_only=False)["data_binding"]
            self.assertEqual(before, after)
            self.assertNotEqual(build_data_binding("数据 a", 0.5), build_data_binding("数据a", 0.5))

    def test_prepared_source_matches_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            target = root / "branch"
            args = tiny_resume_args(checkpoint, data, 3) + ["--prepared-data", str(data), "--out-dir", str(target)]
            self.assertEqual(train.main(args), 0)
            config = json.loads((target / "train_config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["data_source"]["kind"], "prepared_data")

    def test_directory_uses_prepared_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "part.txt").write_bytes(data.read_bytes())
            text, _, _ = train.load_training_text(train.parse_args(["--data-dir", str(corpus)]))
            data.write_text(text, encoding="utf-8")
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            args = tiny_resume_args(checkpoint, data, 3) + [
                "--data-dir",
                str(corpus),
                "--out-dir",
                str(root / "branch"),
            ]
            self.assertEqual(train.main(args), 0)
            state = torch.load(root / "branch/checkpoint.pt", map_location="cpu", weights_only=False)
            self.assertEqual(state["data_binding"], build_data_binding(text, 0.5))


if __name__ == "__main__":
    unittest.main()
