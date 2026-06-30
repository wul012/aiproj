from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

from scripts import serve_playground

ensure_src_path()


class ServingCliBehaviorTests(unittest.TestCase):
    def test_serve_playground_main_prints_endpoints_with_fake_server(self) -> None:
        class FakeServer:
            server_port = 4321

            def __init__(self) -> None:
                self.served = False
                self.closed = False

            def serve_forever(self) -> None:
                self.served = True

            def server_close(self) -> None:
                self.closed = True

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint_path = root / "checkpoint.pt"
            tokenizer_path = root / "tokenizer.json"
            request_log_path = root / "requests.jsonl"
            checkpoint_path.write_bytes(b"fake")
            tokenizer_path.write_text("{}", encoding="utf-8")
            fake_server = FakeServer()
            calls: dict[str, object] = {}

            def fake_run_server(*args: object, **kwargs: object) -> FakeServer:
                calls["run_server_args"] = args
                calls["run_server_kwargs"] = kwargs
                return fake_server

            def fake_discover_checkpoint_options(*args: object, **kwargs: object) -> list[dict[str, object]]:
                calls["discover_args"] = args
                calls["discover_kwargs"] = kwargs
                return [{"path": str(checkpoint_path), "exists": True}]

            original_run_server = serve_playground.run_server
            original_discover = serve_playground.discover_checkpoint_options
            serve_playground.run_server = fake_run_server
            serve_playground.discover_checkpoint_options = fake_discover_checkpoint_options
            try:
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    exit_code = serve_playground.main(
                        [
                            "--run-dir",
                            str(root),
                            "--checkpoint",
                            str(checkpoint_path),
                            "--tokenizer",
                            str(tokenizer_path),
                            "--host",
                            "127.0.0.1",
                            "--port",
                            "0",
                            "--device",
                            "cpu",
                            "--max-prompt-chars",
                            "12",
                            "--max-new-tokens-limit",
                            "7",
                            "--max-top-k",
                            "5",
                            "--request-log",
                            str(request_log_path),
                        ]
                    )
            finally:
                serve_playground.run_server = original_run_server
                serve_playground.discover_checkpoint_options = original_discover

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertTrue(fake_server.served)
            self.assertTrue(fake_server.closed)
            self.assertIn("serving=http://127.0.0.1:4321/", output)
            self.assertIn("model_info=http://127.0.0.1:4321/api/model-info", output)
            self.assertIn("checkpoint_count=1", output)
            self.assertIn(f"request_log={request_log_path}", output)
            self.assertIn("'max_prompt_chars': 12", output)
            self.assertIn("'max_new_tokens': 7", output)
            self.assertIn("'max_top_k': 5", output)

            kwargs = calls["run_server_kwargs"]
            self.assertIsInstance(kwargs, dict)
            self.assertEqual(kwargs["host"], "127.0.0.1")
            self.assertEqual(kwargs["port"], 0)
            self.assertEqual(kwargs["checkpoint_path"], checkpoint_path)
            self.assertEqual(kwargs["tokenizer_path"], tokenizer_path)
            self.assertEqual(kwargs["device"], "cpu")
            self.assertEqual(kwargs["request_log_path"], request_log_path)


if __name__ == "__main__":
    unittest.main()
