from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from tests._bootstrap import ensure_src_path

from minigpt.training.rng_state import capture_rng_state, restore_rng_state
from minigpt.training.history_recovery import recover_history, snapshot_history
from scripts import train
from tests.model_cli_fixtures import make_tiny_checkpoint, tiny_resume_args
from tests.test_checkpoint_io import fail_save

ensure_src_path()


def file_bytes(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class HistoryRecoveryTests(unittest.TestCase):
    def test_partial_suffix_and_idempotence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "metrics.jsonl"
            prefix = '{"step":2,"note":"训练"}\r\n'.encode()
            path.write_bytes(prefix)
            checkpoint = {"history_state": snapshot_history(path)}
            original = prefix + b'\xe4{"step":3'
            path.write_bytes(original)
            backup = recover_history(path, checkpoint)
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(path.read_bytes(), prefix)
            before = file_bytes(root)
            self.assertIsNone(recover_history(path, checkpoint))
            self.assertEqual(file_bytes(root), before)

    def test_invalid_metadata_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "metrics.jsonl"
            path.write_bytes(b"committed\n")
            state = snapshot_history(path)
            cases = [None, [], {}, state | {"version": 2}, state | {"version": True}]
            cases += [state | {"size": value} for value in (-1, True, "10", 100)]
            cases += [state | {"sha256": value} for value in (None, "0" * 64)]
            path.write_bytes(path.read_bytes() + b"extra\n")
            before = file_bytes(root)
            for case in cases:
                with self.subTest(state=case), self.assertRaises(ValueError):
                    recover_history(path, {"history_state": case})
                self.assertEqual(file_bytes(root), before)

    def test_changed_or_missing_prefix_fails(self) -> None:
        for content in (b"tampered!\n", b"short", None):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "metrics.jsonl"
                path.write_bytes(b"committed\n")
                checkpoint = {"history_state": snapshot_history(path)}
                if content is None:
                    path.unlink()
                else:
                    path.write_bytes(content)
                before = file_bytes(root)
                with self.assertRaisesRegex(ValueError, "history prefix"):
                    recover_history(path, checkpoint)
                self.assertEqual(file_bytes(root), before)

    def test_legacy_and_empty_are_noops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metrics.jsonl"
            checkpoint = {"history_state": snapshot_history(path)}
            self.assertEqual(checkpoint["history_state"]["size"], 0)
            self.assertIsNone(recover_history(path, checkpoint))
            self.assertFalse(path.exists())
            path.write_bytes(b"unverified legacy history")
            self.assertIsNone(recover_history(path, {}))
            self.assertEqual(path.read_bytes(), b"unverified legacy history")

    def test_backup_conflict_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "metrics.jsonl"
            path.write_bytes(b"prefix\n")
            checkpoint = {"history_state": snapshot_history(path)}
            data = b"prefix\nsuffix\n"
            path.write_bytes(data)
            name = f"metrics-{hashlib.sha256(data).hexdigest()[:12]}.jsonl"
            (root / name).write_bytes(b"belongs to another recovery")
            before = file_bytes(root)
            with self.assertRaisesRegex(ValueError, "backup conflict"):
                recover_history(path, checkpoint)
            self.assertEqual(file_bytes(root), before)

    def test_write_failure_can_be_retried(self) -> None:
        for fail_backup in (True, False):
            with self.subTest(backup=fail_backup), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / "metrics.jsonl"
                prefix = b"prefix\n"
                path.write_bytes(prefix)
                checkpoint = {"history_state": snapshot_history(path)}
                data = prefix + b"suffix\n"
                path.write_bytes(data)
                replace = os.replace

                def fail_replace(source, target):
                    if (target != path) == fail_backup:
                        raise OSError("injected publication failure")
                    replace(source, target)

                with patch("minigpt.training.checkpoint_io.os.replace", side_effect=fail_replace):
                    with self.assertRaisesRegex(OSError, "injected publication"):
                        recover_history(path, checkpoint)
                self.assertEqual(path.read_bytes(), data)
                self.assertEqual(list(root.glob(".*.tmp")), [])
                backup = recover_history(path, checkpoint)
                self.assertEqual(path.read_bytes(), prefix)
                self.assertEqual(backup.read_bytes(), data)
                self.assertEqual(len(list(root.glob("metrics-*.jsonl"))), 1)


class HistoryResumeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(restore_rng_state, capture_rng_state())
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)

    def test_failed_save_retry_has_no_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            history = root / "metrics.jsonl"
            original = checkpoint.read_bytes()
            with patch("torch.save", side_effect=fail_save), self.assertRaises(OSError):
                train.main(tiny_resume_args(checkpoint, data, 3))
            failed_history = history.read_bytes()
            self.assertEqual(checkpoint.read_bytes(), original)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 3)), 0)
            rows = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["step"] for row in rows], [2, 3])
            backups = list(root.glob("metrics-*.jsonl"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), failed_history)
            summary = json.loads((root / "history_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["record_count"], 2)

    def test_bad_prefix_stops_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            checkpoint, _, data, _ = make_tiny_checkpoint(root)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            (root / "metrics.jsonl").write_bytes(b"tampered")
            before = file_bytes(root)
            with self.assertRaisesRegex(ValueError, "history prefix"):
                train.main(tiny_resume_args(checkpoint, data, 3))
            self.assertEqual(file_bytes(root), before)

    def test_other_directory_keeps_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            source, destination = root / "source", root / "branch"
            source.mkdir()
            checkpoint, _, data, _ = make_tiny_checkpoint(source)
            self.assertEqual(train.main(tiny_resume_args(checkpoint, data, 2)), 0)
            with (source / "metrics.jsonl").open("ab") as stream:
                stream.write(b"incomplete suffix")
            before = file_bytes(source)
            args = tiny_resume_args(checkpoint, data, 3) + ["--out-dir", str(destination)]
            self.assertEqual(train.main(args), 0)
            self.assertEqual(file_bytes(source), before)
            rows = (destination / "metrics.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual([json.loads(row)["step"] for row in rows], [3])


if __name__ == "__main__":
    unittest.main()
