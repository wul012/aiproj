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
    InferenceSafetyProfile,
    append_inference_log,
    build_checkpoints_payload,
    build_health_payload,
    build_model_info_payload,
    create_handler,
    discover_checkpoint_options,
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
        self.assertIsNone(request.checkpoint)

    def test_parse_generation_request_rejects_bad_values(self) -> None:
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "", "max_new_tokens": 12})
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "x", "temperature": 0})
        with self.assertRaises(ValueError):
            parse_generation_request({"prompt": "x", "max_new_tokens": 900})

    def test_parse_generation_request_uses_safety_profile(self) -> None:
        safety = InferenceSafetyProfile(max_prompt_chars=4, max_new_tokens=8, min_temperature=0.2, max_temperature=1.0, max_top_k=20)

        request = parse_generation_request({"prompt": "abcd", "max_new_tokens": 8, "temperature": 1.0, "top_k": 20}, safety)

        self.assertEqual(request.max_new_tokens, 8)
        with self.assertRaisesRegex(ValueError, "prompt must be at most"):
            parse_generation_request({"prompt": "abcde"}, safety)
        with self.assertRaisesRegex(ValueError, "max_new_tokens"):
            parse_generation_request({"prompt": "x", "max_new_tokens": 9}, safety)
        with self.assertRaisesRegex(ValueError, "temperature"):
            parse_generation_request({"prompt": "x", "max_new_tokens": 8, "temperature": 1.5}, safety)
        with self.assertRaisesRegex(ValueError, "top_k"):
            parse_generation_request({"prompt": "x", "max_new_tokens": 8, "top_k": 21}, safety)

    def test_health_payload_marks_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            safety = InferenceSafetyProfile(max_prompt_chars=123)

            health = build_health_payload(run_dir, safety_profile=safety, request_log_path=run_dir / "requests.jsonl")

            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["checkpoint_exists"])
            self.assertTrue(health["tokenizer_exists"])
            self.assertEqual(health["safety"]["max_prompt_chars"], 123)
            self.assertEqual(health["model_info_endpoint"], "/api/model-info")
            self.assertEqual(Path(health["request_log"]).name, "requests.jsonl")
            self.assertEqual(health["checkpoints_endpoint"], "/api/checkpoints")
            self.assertEqual(health["checkpoint_count"], 1)

    def test_discover_checkpoint_options_finds_default_and_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"default")
            candidate = run_dir / "candidate" / "checkpoint.pt"
            candidate.parent.mkdir()
            candidate.write_bytes(b"candidate")
            extra = run_dir / "checkpoints" / "wide.pt"
            extra.parent.mkdir()
            extra.write_bytes(b"wide")

            options = discover_checkpoint_options(run_dir)
            payload = build_checkpoints_payload(run_dir)

            self.assertEqual(options[0].id, "default")
            self.assertTrue(options[0].is_default)
            self.assertIn("candidate", {option.id for option in options})
            self.assertIn("checkpoints-wide", {option.id for option in options})
            self.assertEqual(payload["default_checkpoint_id"], "default")
            self.assertGreaterEqual(payload["checkpoint_count"], 3)

    def test_model_info_payload_reads_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": "char"}), encoding="utf-8")
            (run_dir / "dataset_version.json").write_text(
                json.dumps({"dataset": {"id": "demo@v1"}, "stats": {"short_fingerprint": "abc123"}}),
                encoding="utf-8",
            )
            (run_dir / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "git": {"short_commit": "abc1234"},
                        "training": {"tokenizer": "char"},
                        "model": {"parameter_count": 42, "config": {"n_layer": 1}},
                        "data": {"dataset_version": {"id": "demo@v1", "short_fingerprint": "abc123"}},
                        "artifacts": [{"exists": True}, {"exists": False}],
                    }
                ),
                encoding="utf-8",
            )

            info = build_model_info_payload(run_dir)

            self.assertEqual(info["status"], "ok")
            self.assertIsNone(info["checkpoint_id"])
            self.assertTrue(info["checkpoint_exists"])
            self.assertEqual(info["tokenizer"], "char")
            self.assertEqual(info["model_config"], {"n_layer": 1})
            self.assertEqual(info["parameter_count"], 42)
            self.assertEqual(info["dataset_version"], "demo@v1")
            self.assertEqual(info["dataset_fingerprint"], "abc123")
            self.assertEqual(info["artifact_count"], 1)

    def test_append_inference_log_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "logs" / "requests.jsonl"

            append_inference_log(log_path, {"endpoint": "/api/generate", "status": "ok"})

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["endpoint"], "/api/generate")
            self.assertEqual(record["status"], "ok")
            self.assertIn("timestamp", record)

    def test_http_health_and_generate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            candidate = run_dir / "candidate" / "checkpoint.pt"
            candidate.parent.mkdir()
            candidate.write_bytes(b"candidate")
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                health = _get_json(base + "/api/health")
                self.assertTrue(health["checkpoint_exists"])
                self.assertEqual(health["safety"]["max_new_tokens"], 512)
                self.assertEqual(health["default_checkpoint_id"], "default")

                info = _get_json(base + "/api/model-info")
                self.assertEqual(info["status"], "ok")
                self.assertTrue(info["checkpoint_exists"])
                self.assertEqual(info["checkpoint_id"], "default")

                checkpoints = _get_json(base + "/api/checkpoints")
                self.assertEqual(checkpoints["default_checkpoint_id"], "default")
                self.assertTrue(any(item["id"] == "candidate" for item in checkpoints["checkpoints"]))

                candidate_info = _get_json(base + "/api/model-info?checkpoint=candidate")
                self.assertEqual(candidate_info["checkpoint_id"], "candidate")

                response = _post_json(
                    base + "/api/generate",
                    {"prompt": "abc", "max_new_tokens": 5, "temperature": 0.8, "top_k": 0, "seed": 7, "checkpoint": "candidate"},
                )
                self.assertEqual(response["generated"], "abc::generated")
                self.assertIsNone(response["top_k"])
                self.assertEqual(response["checkpoint_id"], "candidate")
                self.assertTrue(response["checkpoint"].endswith(str(Path("candidate") / "checkpoint.pt")))
                log_path = run_dir / "inference_requests.jsonl"
                self.assertTrue(log_path.exists())
                log_record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(log_record["status"], "ok")
                self.assertEqual(log_record["prompt_chars"], 3)
                self.assertEqual(log_record["checkpoint_id"], "candidate")
                self.assertEqual(log_record["requested_checkpoint"], "candidate")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_rejects_bad_generate_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            safety = InferenceSafetyProfile(max_prompt_chars=4, max_body_bytes=64)
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator, safety_profile=safety)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaises(HTTPError) as cm:
                    _post_json(f"http://127.0.0.1:{server.server_port}/api/generate", {"prompt": ""})
                self.assertEqual(cm.exception.code, 400)
                with self.assertRaises(HTTPError) as cm:
                    _post_json(f"http://127.0.0.1:{server.server_port}/api/generate", {"prompt": "abcde"})
                self.assertEqual(cm.exception.code, 400)
                log_records = [
                    json.loads(line)
                    for line in (run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").splitlines()
                ]
                self.assertTrue(all(record["status"] == "bad_request" for record in log_records))
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
