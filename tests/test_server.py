from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.server import (
    GenerationResponse,
    GenerationStreamChunk,
    InferenceSafetyProfile,
    append_inference_log,
    build_checkpoint_compare_payload,
    build_checkpoints_payload,
    build_health_payload,
    build_model_info_payload,
    build_request_history_detail_payload,
    build_request_history_payload,
    create_handler,
    discover_checkpoint_options,
    parse_generation_pair_request,
    parse_generation_request,
    request_history_to_csv,
    sse_message,
    stream_timeout_payload,
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

    def stream(self, request):
        generated = request.prompt
        continuation = ""
        for index, text in enumerate(["::", "generated"]):
            generated += text
            continuation += text
            yield GenerationStreamChunk(
                index=index,
                token_id=100 + index,
                text=text,
                generated=generated,
                continuation=continuation,
                checkpoint=self.checkpoint,
                tokenizer="stub",
            )


class SlowStreamGenerator(StubGenerator):
    def stream(self, request):
        generated = request.prompt
        continuation = ""
        for index, text in enumerate(["a", "b", "c"]):
            time.sleep(0.02)
            generated += text
            continuation += text
            yield GenerationStreamChunk(
                index=index,
                token_id=200 + index,
                text=text,
                generated=generated,
                continuation=continuation,
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

    def test_parse_generation_pair_request(self) -> None:
        request = parse_generation_pair_request(
            {
                "prompt": "hello",
                "max_new_tokens": "12",
                "temperature": "0.7",
                "top_k": "0",
                "seed": "5",
                "left_checkpoint": "default",
                "right_checkpoint": "wide",
            }
        )

        self.assertEqual(request.left.prompt, "hello")
        self.assertEqual(request.left.checkpoint, "default")
        self.assertEqual(request.right.checkpoint, "wide")
        self.assertIsNone(request.right.top_k)
        with self.assertRaisesRegex(ValueError, "right_checkpoint"):
            parse_generation_pair_request({"prompt": "hello", "left_checkpoint": "default"})

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
            self.assertEqual(health["generate_pair_endpoint"], "/api/generate-pair")
            self.assertEqual(health["generate_pair_artifact_endpoint"], "/api/generate-pair-artifact")
            self.assertEqual(health["request_history_endpoint"], "/api/request-history")
            self.assertEqual(Path(health["request_log"]).name, "requests.jsonl")
            self.assertEqual(health["checkpoints_endpoint"], "/api/checkpoints")
            self.assertEqual(health["checkpoint_compare_endpoint"], "/api/checkpoint-compare")
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

    def test_checkpoint_compare_payload_adds_metadata_and_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"default")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            (run_dir / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "training": {"tokenizer": "char"},
                        "model": {"parameter_count": 100, "config": {"n_layer": 1}},
                        "data": {"dataset_version": {"id": "demo@v1", "short_fingerprint": "aaa111"}},
                    }
                ),
                encoding="utf-8",
            )
            wide = run_dir / "wide"
            wide.mkdir()
            (wide / "checkpoint.pt").write_bytes(b"wide-model")
            (wide / "tokenizer.json").write_text("{}", encoding="utf-8")
            (wide / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "training": {"tokenizer": "bpe"},
                        "model": {"parameter_count": 150, "config": {"n_layer": 2}},
                        "data": {"dataset_version": {"id": "demo@v2", "short_fingerprint": "bbb222"}},
                    }
                ),
                encoding="utf-8",
            )

            payload = build_checkpoint_compare_payload(run_dir)
            rows = {row["id"]: row for row in payload["checkpoints"]}

            self.assertEqual(payload["summary"]["ready_count"], 2)
            self.assertEqual(rows["default"]["parameter_delta"], 0)
            self.assertEqual(rows["wide"]["parameter_count"], 150)
            self.assertEqual(rows["wide"]["parameter_delta"], 50)
            self.assertEqual(rows["wide"]["dataset_version"], "demo@v2")
            self.assertFalse(rows["wide"]["same_dataset_version"])
            self.assertFalse(rows["wide"]["same_model_config"])
            self.assertTrue(rows["wide"]["model_info_endpoint"].endswith("checkpoint=wide"))

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

    def test_request_history_payload_reads_recent_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate",
                    "status": "ok",
                    "checkpoint_id": "default",
                    "prompt_chars": 3,
                    "generated_chars": 12,
                },
            )
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "timeout",
                    "checkpoint_id": "default",
                    "prompt_chars": 4,
                    "generated_chars": 8,
                    "stream_chunks": 2,
                    "stream_timed_out": True,
                    "stream_elapsed_seconds": 0.5,
                },
            )
            log_path.write_text(log_path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "cancelled",
                    "checkpoint_id": "wide",
                    "prompt_chars": 5,
                    "stream_chunks": 1,
                    "stream_cancelled": True,
                },
            )

            payload = build_request_history_payload(log_path, limit=2)

            self.assertEqual(payload["status"], "ok")
            self.assertTrue(payload["request_log_exists"])
            self.assertEqual(payload["limit"], 2)
            self.assertEqual(payload["total_log_records"], 3)
            self.assertEqual(payload["invalid_record_count"], 1)
            self.assertEqual(payload["record_count"], 2)
            self.assertEqual(payload["requests"][0]["status"], "cancelled")
            self.assertEqual(payload["requests"][0]["log_index"], 4)
            self.assertEqual(payload["requests"][1]["status"], "timeout")
            self.assertEqual(payload["requests"][1]["log_index"], 2)
            self.assertEqual(payload["summary"]["timeout_count"], 1)
            self.assertEqual(payload["summary"]["cancelled_count"], 1)
            self.assertEqual(payload["summary"]["returned_endpoint_counts"]["/api/generate-stream"], 2)
            self.assertNotIn("generated", payload["requests"][0])
            with self.assertRaisesRegex(ValueError, "limit"):
                build_request_history_payload(log_path, limit=0)

    def test_request_history_payload_filters_and_exports_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate",
                    "status": "ok",
                    "checkpoint_id": "default",
                    "requested_checkpoint": "default",
                    "prompt_chars": 3,
                    "generated_chars": 10,
                },
            )
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "timeout",
                    "checkpoint_id": "wide",
                    "requested_checkpoint": "wide",
                    "prompt_chars": 4,
                    "generated_chars": 11,
                    "stream_chunks": 2,
                    "stream_timed_out": True,
                },
            )
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-pair",
                    "status": "ok",
                    "left_checkpoint_id": "default",
                    "right_checkpoint_id": "wide",
                    "requested_right_checkpoint": "wide",
                    "prompt_chars": 5,
                    "left_generated_chars": 12,
                    "right_generated_chars": 13,
                    "generated_equal": False,
                },
            )

            payload = build_request_history_payload(
                log_path,
                limit=10,
                status_filter="ok",
                checkpoint_filter="wide",
            )
            csv_text = request_history_to_csv(payload["requests"])

            self.assertEqual(payload["matching_log_records"], 1)
            self.assertEqual(payload["record_count"], 1)
            self.assertEqual(payload["filters"]["status"], "ok")
            self.assertEqual(payload["filters"]["checkpoint"], "wide")
            self.assertEqual(payload["requests"][0]["endpoint"], "/api/generate-pair")
            self.assertEqual(payload["requests"][0]["log_index"], 3)
            self.assertIn("log_index,timestamp,endpoint,status,checkpoint_id", csv_text)
            self.assertIn("/api/generate-pair", csv_text)
            self.assertIn("false", csv_text)

            endpoint_payload = build_request_history_payload(log_path, endpoint_filter="/api/generate-stream")
            self.assertEqual(endpoint_payload["matching_log_records"], 1)
            self.assertEqual(endpoint_payload["requests"][0]["status"], "timeout")

    def test_request_history_detail_payload_reads_original_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "requests.jsonl"
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate",
                    "status": "ok",
                    "checkpoint_id": "default",
                    "prompt_chars": 3,
                    "generated_chars": 10,
                },
            )
            log_path.write_text(log_path.read_text(encoding="utf-8") + "{broken\n", encoding="utf-8")
            append_inference_log(
                log_path,
                {
                    "endpoint": "/api/generate-stream",
                    "status": "timeout",
                    "checkpoint_id": "wide",
                    "prompt_chars": 4,
                    "stream_chunks": 2,
                    "stream_timed_out": True,
                },
            )

            detail = build_request_history_detail_payload(log_path, log_index=3)

            self.assertEqual(detail["status"], "ok")
            self.assertEqual(detail["log_index"], 3)
            self.assertEqual(detail["total_log_records"], 2)
            self.assertEqual(detail["invalid_record_count"], 1)
            self.assertEqual(detail["normalized"]["log_index"], 3)
            self.assertEqual(detail["normalized"]["endpoint"], "/api/generate-stream")
            self.assertEqual(detail["record"]["checkpoint_id"], "wide")
            self.assertTrue(detail["record"]["stream_timed_out"])
            with self.assertRaisesRegex(ValueError, "log_index"):
                build_request_history_detail_payload(log_path, log_index=0)
            with self.assertRaisesRegex(LookupError, "not found"):
                build_request_history_detail_payload(log_path, log_index=2)

    def test_sse_message_formats_event_and_json_data(self) -> None:
        message = sse_message("token", {"text": "中", "index": 1}).decode("utf-8")

        self.assertEqual(message, 'event: token\ndata: {"text": "中", "index": 1}\n\n')

    def test_stream_timeout_payload_keeps_partial_response(self) -> None:
        request = parse_generation_request({"prompt": "abc", "max_new_tokens": 5})

        payload = stream_timeout_payload(
            request,
            elapsed_seconds=1.2345678,
            max_stream_seconds=1.0,
            chunk_count=2,
            generated="abcde",
            continuation="de",
            checkpoint="checkpoint.pt",
            tokenizer="char",
            checkpoint_id="default",
        )

        self.assertFalse(payload["done"])
        self.assertEqual(payload["reason"], "timeout")
        self.assertEqual(payload["elapsed_seconds"], 1.234568)
        self.assertEqual(payload["chunk_count"], 2)
        self.assertEqual(payload["response"]["generated"], "abcde")
        self.assertEqual(payload["response"]["checkpoint_id"], "default")

    def test_log_generation_can_record_cancelled_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator)

            class Harness(handler):
                def __init__(self) -> None:
                    self.client_address = ("127.0.0.1", 12345)

            harness = Harness()
            request = parse_generation_request({"prompt": "abc", "max_new_tokens": 5})
            response = GenerationResponse("abc", "abc::", "::", 5, 0.8, 30, None, "checkpoint.pt", "stub", "default")

            harness._log_generation(
                "cancelled",
                request=request,
                response=response,
                endpoint="/api/generate-stream",
                stream_chunks=1,
                stream_timed_out=False,
                stream_cancelled=True,
                stream_elapsed_seconds=0.25,
            )

            record = json.loads((run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").strip())
            self.assertEqual(record["status"], "cancelled")
            self.assertEqual(record["endpoint"], "/api/generate-stream")
            self.assertEqual(record["stream_chunks"], 1)
            self.assertEqual(record["stream_cancelled"], True)
            self.assertEqual(record["stream_timed_out"], False)
            self.assertEqual(record["stream_elapsed_seconds"], 0.25)

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
                self.assertEqual(health["safety"]["max_stream_seconds"], 30.0)
                self.assertEqual(health["default_checkpoint_id"], "default")
                self.assertEqual(health["generate_stream_endpoint"], "/api/generate-stream")
                self.assertEqual(health["generate_pair_endpoint"], "/api/generate-pair")
                self.assertEqual(health["generate_pair_artifact_endpoint"], "/api/generate-pair-artifact")
                self.assertEqual(health["checkpoint_compare_endpoint"], "/api/checkpoint-compare")
                self.assertEqual(health["request_history_endpoint"], "/api/request-history")
                self.assertEqual(health["request_history_detail_endpoint"], "/api/request-history-detail")

                info = _get_json(base + "/api/model-info")
                self.assertEqual(info["status"], "ok")
                self.assertTrue(info["checkpoint_exists"])
                self.assertEqual(info["checkpoint_id"], "default")

                checkpoints = _get_json(base + "/api/checkpoints")
                self.assertEqual(checkpoints["default_checkpoint_id"], "default")
                self.assertTrue(any(item["id"] == "candidate" for item in checkpoints["checkpoints"]))

                compare = _get_json(base + "/api/checkpoint-compare")
                self.assertEqual(compare["default_checkpoint_id"], "default")
                self.assertTrue(any(item["id"] == "candidate" for item in compare["checkpoints"]))

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
                history = _get_json(base + "/api/request-history?limit=5")
                self.assertEqual(history["status"], "ok")
                self.assertEqual(history["record_count"], 1)
                self.assertEqual(history["requests"][0]["endpoint"], "/api/generate")
                self.assertEqual(history["requests"][0]["checkpoint_id"], "candidate")
                self.assertEqual(history["requests"][0]["log_index"], 1)
                detail = _get_json(base + "/api/request-history-detail?log_index=1")
                self.assertEqual(detail["status"], "ok")
                self.assertEqual(detail["normalized"]["checkpoint_id"], "candidate")
                self.assertEqual(detail["record"]["requested_checkpoint"], "candidate")
                filtered = _get_json(base + "/api/request-history?status=ok&endpoint=/api/generate&checkpoint=candidate")
                self.assertEqual(filtered["matching_log_records"], 1)
                self.assertEqual(filtered["filters"]["checkpoint"], "candidate")
                csv_text, csv_content_type = _get_raw(base + "/api/request-history?status=ok&format=csv")
                self.assertTrue(csv_content_type.startswith("text/csv"))
                self.assertIn("log_index,timestamp,endpoint,status,checkpoint_id", csv_text)
                self.assertIn("/api/generate", csv_text)
                with self.assertRaises(HTTPError) as missing_index:
                    _get_json(base + "/api/request-history-detail")
                self.assertEqual(missing_index.exception.code, 400)
                with self.assertRaises(HTTPError) as missing_record:
                    _get_json(base + "/api/request-history-detail?log_index=9")
                self.assertEqual(missing_record.exception.code, 404)
                with self.assertRaises(HTTPError) as cm:
                    _get_json(base + "/api/request-history?limit=999")
                self.assertEqual(cm.exception.code, 400)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_generate_stream_sends_sse_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            handler = create_handler(run_dir, device="cpu", generator_factory=StubGenerator)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                body, content_type = _post_raw(
                    base + "/api/generate-stream",
                    {"prompt": "abc", "max_new_tokens": 5, "temperature": 0.8, "top_k": 0, "seed": 7},
                )

                self.assertTrue(content_type.startswith("text/event-stream"))
                events = _parse_sse(body)
                self.assertEqual([event["event"] for event in events], ["start", "token", "token", "end"])
                self.assertEqual(events[0]["data"]["prompt"], "abc")
                self.assertEqual(events[1]["data"]["text"], "::")
                self.assertEqual(events[2]["data"]["generated"], "abc::generated")
                self.assertEqual(events[-1]["data"]["chunk_count"], 2)
                self.assertEqual(events[-1]["data"]["response"]["generated"], "abc::generated")
                log_record = json.loads((run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(log_record["endpoint"], "/api/generate-stream")
                self.assertEqual(log_record["status"], "ok")
                self.assertEqual(log_record["stream_chunks"], 2)
                self.assertEqual(log_record["generated_chars"], len("abc::generated"))
                history = _get_json(base + "/api/request-history?limit=1")
                self.assertEqual(history["requests"][0]["endpoint"], "/api/generate-stream")
                self.assertEqual(history["requests"][0]["stream_chunks"], 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_generate_stream_times_out_and_logs_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "checkpoint.pt").write_bytes(b"fake")
            safety = InferenceSafetyProfile(max_stream_seconds=0.01)
            handler = create_handler(run_dir, device="cpu", generator_factory=SlowStreamGenerator, safety_profile=safety)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                body, content_type = _post_raw(
                    base + "/api/generate-stream",
                    {"prompt": "abc", "max_new_tokens": 5, "temperature": 0.8, "top_k": 0, "seed": 7},
                )

                self.assertTrue(content_type.startswith("text/event-stream"))
                events = _parse_sse(body)
                self.assertEqual([event["event"] for event in events], ["start", "token", "timeout"])
                self.assertEqual(events[-1]["data"]["reason"], "timeout")
                self.assertFalse(events[-1]["data"]["done"])
                self.assertEqual(events[-1]["data"]["chunk_count"], 1)
                self.assertEqual(events[-1]["data"]["response"]["generated"], "abca")
                log_record = json.loads((run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(log_record["endpoint"], "/api/generate-stream")
                self.assertEqual(log_record["status"], "timeout")
                self.assertTrue(log_record["stream_timed_out"])
                self.assertEqual(log_record["stream_chunks"], 1)
                self.assertGreaterEqual(log_record["stream_elapsed_seconds"], 0.01)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_http_generate_pair_routes_two_checkpoints(self) -> None:
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
                response = _post_json(
                    base + "/api/generate-pair",
                    {
                        "prompt": "abc",
                        "max_new_tokens": 5,
                        "temperature": 0.8,
                        "top_k": 0,
                        "seed": 7,
                        "left_checkpoint": "default",
                        "right_checkpoint": "candidate",
                    },
                )

                self.assertEqual(response["status"], "ok")
                self.assertEqual(response["left"]["checkpoint_id"], "default")
                self.assertEqual(response["right"]["checkpoint_id"], "candidate")
                self.assertEqual(response["comparison"]["same_checkpoint"], False)
                log_record = json.loads((run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(log_record["endpoint"], "/api/generate-pair")
                self.assertEqual(log_record["status"], "ok")
                self.assertEqual(log_record["left_checkpoint_id"], "default")
                self.assertEqual(log_record["right_checkpoint_id"], "candidate")
                self.assertEqual(log_record["requested_right_checkpoint"], "candidate")

                saved = _post_json(
                    base + "/api/generate-pair-artifact",
                    {
                        "prompt": "abc",
                        "max_new_tokens": 5,
                        "temperature": 0.8,
                        "top_k": 0,
                        "seed": 8,
                        "left_checkpoint": "default",
                        "right_checkpoint": "candidate",
                    },
                )
                artifact = saved["artifact"]
                json_path = Path(artifact["json_path"])
                html_path = Path(artifact["html_path"])
                self.assertTrue(json_path.exists())
                self.assertTrue(html_path.exists())
                record = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertEqual(record["kind"], "minigpt_pair_generation")
                self.assertEqual(record["right"]["checkpoint_id"], "candidate")
                self.assertIn("abc::generated", html_path.read_text(encoding="utf-8"))
                artifact_log = json.loads((run_dir / "inference_requests.jsonl").read_text(encoding="utf-8").splitlines()[-1])
                self.assertEqual(artifact_log["endpoint"], "/api/generate-pair-artifact")
                self.assertEqual(artifact_log["artifact_json"], str(json_path))
                self.assertEqual(artifact_log["artifact_html"], str(html_path))
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


def _get_raw(url: str) -> tuple[str, str]:
    with urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8"), response.headers.get("Content-Type", "")


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_raw(url: str, payload: dict) -> tuple[str, str]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return response.read().decode("utf-8"), response.headers.get("Content-Type", "")


def _parse_sse(body: str) -> list[dict]:
    events = []
    for block in body.strip().split("\n\n"):
        event_name = "message"
        data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event_name = line.partition(":")[2].strip()
            if line.startswith("data:"):
                data = json.loads(line.partition(":")[2].strip())
        events.append({"event": event_name, "data": data})
    return events


if __name__ == "__main__":
    unittest.main()
