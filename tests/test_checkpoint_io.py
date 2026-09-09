from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.checkpoint_io import save_checkpoint
from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint

ensure_src_path()


def fail_save(payload: dict, target: object) -> None:
    if hasattr(target, "write"):
        target.write(b"incomplete checkpoint")
    else:
        Path(target).write_bytes(b"incomplete checkpoint")
    raise OSError("injected write failure")


def fault_patch(stage: str):
    error = OSError("injected write failure")
    module = "minigpt.training.checkpoint_io"
    if stage == "serialize":
        return patch(f"{module}.torch.save", side_effect=fail_save)
    if stage == "interrupt":
        return patch(f"{module}.torch.save", side_effect=KeyboardInterrupt("injected interrupt"))
    if stage == "flush":
        factory = tempfile.NamedTemporaryFile

        def fail_flush(*args, **kwargs):
            stream = factory(*args, **kwargs)
            stream.flush = Mock(side_effect=error)
            return stream

        return patch(f"{module}.tempfile.NamedTemporaryFile", side_effect=fail_flush)
    target = {"create": "tempfile.NamedTemporaryFile", "sync": "os.fsync", "replace": "os.replace"}[stage]
    return patch(f"{module}.{target}", side_effect=error)


class CheckpointIoTests(unittest.TestCase):
    def test_killed_writer_keeps_old_file(self) -> None:
        code = """
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from minigpt.training import checkpoint_io
def pause_write(payload, stream):
    stream.write(b'incomplete checkpoint')
    stream.flush()
    Path(sys.argv[2]).write_text('ready', encoding='utf-8')
    time.sleep(60)
checkpoint_io.torch.save = pause_write
checkpoint_io.save_checkpoint({'step': 2}, Path(sys.argv[1]))
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, ready = root / "checkpoint.pt", root / "ready"
            torch.save({"step": 1}, path)
            original = path.read_bytes()
            process = subprocess.Popen(
                [sys.executable, "-B", "-c", code, str(path), str(ready)],
                cwd=Path(__file__).resolve().parents[1],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                deadline = time.monotonic() + 30
                while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), "child did not reach the partial-write boundary")
                self.assertIsNone(process.poll())
            finally:
                if process.poll() is None:
                    process.kill()
                output, _ = process.communicate(timeout=10)
            self.assertNotEqual(process.returncode, 0, output.decode(errors="replace"))
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(torch.load(path, weights_only=False)["step"], 1)
            leftovers = list(root.glob(".checkpoint.pt.*.tmp"))
            self.assertEqual(len(leftovers), 1)
            self.assertEqual(leftovers[0].read_bytes(), b"incomplete checkpoint")

    def test_create_and_replace_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.pt"
            for step in (1, 2):
                with self.subTest(step=step):
                    save_checkpoint({"step": step, "model": torch.tensor([step])}, path)
                    loaded = torch.load(path, map_location="cpu", weights_only=False)
                    self.assertEqual(loaded["step"], step)
                    self.assertTrue(torch.equal(loaded["model"], torch.tensor([step])))
                    self.assertEqual(list(root.iterdir()), [path])

    def test_failures_preserve_directory(self) -> None:
        for exists in (False, True):
            for stage in ("create", "serialize", "flush", "sync", "replace", "interrupt"):
                with self.subTest(exists=exists, stage=stage), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    path = root / "checkpoint.pt"
                    orphan = root / ".checkpoint.pt.previous.tmp"
                    orphan.write_bytes(b"not owned by this call")
                    if exists:
                        torch.save({"step": 1}, path)
                    before = {p.name: p.read_bytes() for p in root.iterdir()}
                    error = KeyboardInterrupt if stage == "interrupt" else OSError
                    with fault_patch(stage), self.assertRaisesRegex(error, "injected"):
                        save_checkpoint({"step": 2, "model": torch.zeros(2)}, path)
                    self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)
                    if exists:
                        self.assertEqual(torch.load(path, weights_only=False)["step"], 1)

    def test_sync_close_then_replace(self) -> None:
        events = []
        streams = []
        real_save, real_sync, real_replace = torch.save, os.fsync, os.replace
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.pt"
            real_save({"step": 1}, path)
            original = path.read_bytes()

            def save(payload, stream):
                streams.append(stream)
                real_save(payload, stream)
                events.append("serialize")

            def sync(fd):
                self.assertFalse(streams[0].closed)
                self.assertEqual(streams[0].fileno(), fd)
                real_sync(fd)
                events.append("sync")

            def replace(source, target):
                self.assertEqual(source.parent, target.parent)
                self.assertNotEqual(source, target)
                self.assertTrue(streams[0].closed)
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(torch.load(source, weights_only=False)["step"], 2)
                real_replace(source, target)
                events.append("replace")

            module = "minigpt.training.checkpoint_io"
            with (
                patch(f"{module}.torch.save", side_effect=save),
                patch(f"{module}.os.fsync", side_effect=sync),
                patch(f"{module}.os.replace", side_effect=replace),
            ):
                save_checkpoint({"step": 2}, path)
            self.assertEqual(events, ["serialize", "sync", "replace"])
            self.assertEqual(torch.load(path, weights_only=False)["step"], 2)
            self.assertEqual(list(root.iterdir()), [path])


class TrainSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rng = capture_rng_state()
        self.threads = torch.get_num_threads()
        torch.set_num_threads(1)

    def tearDown(self) -> None:
        restore_rng_state(self.rng)
        torch.set_num_threads(self.threads)

    def run_train(self, checkpoint: Path, data: Path, step: int) -> str:
        args = [
            "--resume",
            str(checkpoint),
            "--data",
            str(data),
            "--max-iters",
            str(step),
            "--batch-size",
            "2",
            "--eval-interval",
            "1",
            "--eval-iters",
            "1",
            "--no-sample",
            "--device",
            "cpu",
            "--train-ratio",
            "0.5",
        ]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(train.main(args), 0)
        return output.getvalue()

    def test_failed_save_can_resume_old_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer, data, _ = make_tiny_checkpoint(root)
            self.run_train(checkpoint, data, 2)
            original = checkpoint.read_bytes()
            old_tokenizer = tokenizer.read_bytes()
            with patch("torch.save", side_effect=fail_save):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    self.run_train(checkpoint, data, 3)
            self.assertEqual(checkpoint.read_bytes(), original)
            self.assertEqual(tokenizer.read_bytes(), old_tokenizer)
            loaded, _, _ = train.load_resume_state(checkpoint, torch.device("cpu"))
            self.assertEqual(loaded["step"], 2)
            self.assertIn("rng_state", loaded)
            self.assertEqual(list(root.glob(".checkpoint.pt.*")), [])
            self.assertIn("saved=", self.run_train(checkpoint, data, 3))
            retried, _, _ = train.load_resume_state(checkpoint, torch.device("cpu"))
            self.assertEqual(retried["step"], 3)


if __name__ == "__main__":
    unittest.main()
