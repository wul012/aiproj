from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server
from minigpt import server_post_routes
from minigpt.server_contracts import CheckpointOption, GenerationResponse, InferenceSafetyProfile


class StubGenerator:
    def generate(self, request):
        return GenerationResponse(
            prompt=request.prompt,
            generated=request.prompt + "::ok",
            continuation="::ok",
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_k=request.top_k,
            seed=request.seed,
            checkpoint="checkpoint.pt",
            tokenizer="stub",
        )


class FakeHandler:
    def __init__(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.sent: tuple[dict, HTTPStatus] | None = None
        self.generation_logs: list[dict] = []
        self.pair_logs: list[dict] = []

    def _read_json_body(self) -> dict:
        return server.read_json_body(self, 16 * 1024)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.sent = (payload, status)

    def _log_generation(self, status: str, **kwargs) -> None:
        self.generation_logs.append({"status": status, **kwargs})

    def _log_pair_generation(self, status: str, **kwargs) -> None:
        self.pair_logs.append({"status": status, **kwargs})


class ServerPostRoutesSplitTests(unittest.TestCase):
    def test_server_facade_reexports_post_route_handler(self) -> None:
        self.assertIs(server.handle_post_request, server_post_routes.handle_post_request)

    def test_generate_route_uses_shared_post_helper(self) -> None:
        option = CheckpointOption("default", "default", "checkpoint.pt", True, True, None, False, "default")
        handler = FakeHandler({"prompt": "hi", "max_new_tokens": 3})

        server_post_routes.handle_post_request(
            handler,
            "/api/generate",
            root=Path("."),
            checkpoint="checkpoint.pt",
            safety=InferenceSafetyProfile(),
            checkpoint_options=[option],
            generator_for=lambda _option: StubGenerator(),
        )

        self.assertIsNotNone(handler.sent)
        payload, status = handler.sent
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["generated"], "hi::ok")
        self.assertEqual(payload["checkpoint_id"], "default")
        self.assertEqual(handler.generation_logs[-1]["status"], "ok")

    def test_pair_artifact_route_writes_artifact_through_helper(self) -> None:
        default = CheckpointOption("default", "default", "checkpoint.pt", True, True, None, False, "default")
        candidate = CheckpointOption("candidate", "candidate", "candidate.pt", True, False, None, False, "candidate")
        handler = FakeHandler({"prompt": "hi", "max_new_tokens": 3, "left_checkpoint": "default", "right_checkpoint": "candidate"})
        with tempfile.TemporaryDirectory() as tmp:
            server_post_routes.handle_post_request(
                handler,
                "/api/generate-pair-artifact",
                root=Path(tmp),
                checkpoint="checkpoint.pt",
                safety=InferenceSafetyProfile(),
                checkpoint_options=[default, candidate],
                generator_for=lambda _option: StubGenerator(),
            )

            self.assertIsNotNone(handler.sent)
            payload, status = handler.sent
            self.assertEqual(status, HTTPStatus.OK)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["artifact"]["json_path"], handler.pair_logs[-1]["artifact"]["json_path"])
            self.assertTrue(Path(payload["artifact"]["json_path"]).exists())


if __name__ == "__main__":
    unittest.main()
