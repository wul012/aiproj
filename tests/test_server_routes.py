from __future__ import annotations

import unittest
from http import HTTPStatus
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt import server
from minigpt import server_routes
from minigpt.server_contracts import CheckpointOption, InferenceSafetyProfile


class FakeHandler:
    def __init__(self) -> None:
        self.sent: tuple[dict, HTTPStatus] | None = None

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.sent = (payload, status)

    def _serve_run_file(self, path: str) -> None:
        self.sent = ({"served": path}, HTTPStatus.OK)


class ServerRoutesSplitTests(unittest.TestCase):
    def test_server_facade_reexports_get_route_handler(self) -> None:
        self.assertIs(server.handle_get_request, server_routes.handle_get_request)

    def test_generation_profiles_endpoint_returns_registry(self) -> None:
        handler = FakeHandler()
        option = CheckpointOption("default", "default", "checkpoint.pt", True, True, None, False, "default")

        server_routes.handle_get_request(
            handler,
            "/api/generation-profiles",
            root=Path("."),
            checkpoint="checkpoint.pt",
            tokenizer_path=None,
            safety=InferenceSafetyProfile(),
            request_log="requests.jsonl",
            checkpoint_candidates=None,
            checkpoint_options=[option],
        )

        self.assertIsNotNone(handler.sent)
        payload, status = handler.sent
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["default_generation_profile_id"], "default")
        self.assertTrue(any(profile["id"] == "suppress_newline_tokens" for profile in payload["profiles"]))


if __name__ == "__main__":
    unittest.main()
