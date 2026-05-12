from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.server import (
    GenerationResponse,
    build_health_payload,
    create_handler,
    parse_generation_request,
)
from http.server import ThreadingHTTPServer


class StubGenerator:
    def __init__(self, checkpoint: str | Path, tokenizer: str | Path | None, device: str) -> None:
        self.checkpoint = str(checkpoint)

    def generate(self, request):
        return GenerationResponse(
            prompt=request.prompt,
            generated=request.prompt + "::generated",
            continuation="::generated",
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_k=request.top_k,
            seed=request.seed,
            checkpoint=self.checkpoint,
            tokenizer="stub",
        )


class ServerTests(unittest.TestCase):
    def test_parse_generation_request(self) -> None:
        request = parse_generation_request(
            {"prompt": "hello", "max_new_tokens": "12", "temperature": "0.7", "top_k": "0", "seed": "5"}
        )

        self.assertEqual(request.prompt, "hello")
        self.assertEqual(request.max_new_tokens, 12)
        self.assertEqual(request.temperature, 0.7)
        self.assertIsNone(request.top_k)
        self.assertEqual(request.seed, 5)

    def test_parse_generation_request_rejects_bad_values(self) -> None:
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "", "max_new_tokens": 12})
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "x", "temperature": 0})
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "x", "max_new_tokens": 900})

    def test_health_payload_marks_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")

            health = build_health_payload(run_dir)

            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["checkpoint_exists"])
            self.assertTrue(health["tokenizer_exists"])

    def test_http_health_and_generate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                health = _get_json(base + "/api/health")
                self.assertTrue(health["checkpoint_exists"])

                response = _post_json(
                    base + "/api/generate",
                    {"prompt": "abc", "max_new_tokens": 5, "temperature": 0.8, "top_k": 0, "seed": 7},
                )
                self.assertEqual(response["generated"], "abc::generated")
                self.assertIsNone(response["top_k"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_rejects_bad_generate_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaises(HTTPError) as cm:
                    _post_json(f"http://127.0.0.1:{server.server_port}/api/generate", {"prompt": ""})
                self.assertEqual(cm.exception.code, 400)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
