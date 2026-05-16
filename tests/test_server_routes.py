from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import server
from minigpt import server_routes


class ServerRoutesSplitTests(unittest.TestCase):
    def test_server_facade_reexports_get_route_handler(self) -> None:
        self.assertIs(server.handle_get_request, server_routes.handle_get_request)


if __name__ == "__main__":
    unittest.main()
