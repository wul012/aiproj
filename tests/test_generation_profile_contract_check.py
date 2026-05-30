from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.generation_profile_contract_check import build_generation_profile_contract_check, resolve_exit_code
from minigpt.generation_profile_contract_check_artifacts import (
    render_generation_profile_contract_check_html,
    render_generation_profile_contract_check_markdown,
    render_generation_profile_contract_check_text,
    write_generation_profile_contract_check_outputs,
)
from scripts.check_generation_profile_contract import main as check_main


class GenerationProfileContractCheckTests(unittest.TestCase):
    def test_valid_contract_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = _write_fixture(Path(tmp))

            report = build_generation_profile_contract_check(**fixture)
            text = render_generation_profile_contract_check_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "generation_profile_contract_ready")
            self.assertEqual(report["failed_count"], 0)
            self.assertIn("failed_count=0", text)
            self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_suppression_profile_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_fixture(root)
            payload = _read_json(root / "generation-profiles.json")
            payload["profiles"] = [profile for profile in payload["profiles"] if profile["id"] != "suppress_newline_tokens"]
            payload["profile_count"] = 1
            _write_json(root / "generation-profiles.json", payload)

            report = build_generation_profile_contract_check(**fixture)

            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(issue["id"] == "profiles_expected_ids" for issue in report["issues"]))

    def test_health_endpoint_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_fixture(root)
            payload = _read_json(root / "health.json")
            payload["generation_profiles_endpoint"] = "/api/old-generation-profiles"
            _write_json(root / "health.json", payload)

            report = build_generation_profile_contract_check(**fixture)

            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(issue["id"] == "health_profiles_endpoint" for issue in report["issues"]))

    def test_api_profile_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_fixture(root)
            payload = _read_json(root / "api.json")
            payload["generation_profile"] = "default"
            _write_json(root / "api.json", payload)

            report = build_generation_profile_contract_check(**fixture)

            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(issue["id"] == "api_generation_profile" for issue in report["issues"]))

    def test_cli_require_pass_returns_one_on_failed_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = _write_fixture(root)
            payload = _read_json(root / "api.json")
            payload["blocked_token_count"] = 0
            _write_json(root / "api.json", payload)

            with self.assertRaises(SystemExit) as raised:
                check_main(
                    [
                        str(fixture["profiles_path"]),
                        "--health",
                        str(fixture["health_path"]),
                        "--api-response",
                        str(fixture["api_response_path"]),
                        "--playground-html",
                        str(fixture["playground_html_path"]),
                        "--default-output",
                        str(fixture["default_output_path"]),
                        "--profile-output",
                        str(fixture["profile_output_path"]),
                        "--out-dir",
                        str(root / "check"),
                        "--require-pass",
                        "--force",
                    ]
                )

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "check" / "generation_profile_contract_check.json").is_file())

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_generation_profile_contract_check(**_write_fixture(root))

            outputs = write_generation_profile_contract_check_outputs(report, root / "check")
            markdown = render_generation_profile_contract_check_markdown(report)
            html = render_generation_profile_contract_check_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("Generation Profile Contract Check", markdown)
            self.assertIn("MiniGPT generation profile contract check", html)


def _write_fixture(root: Path) -> dict[str, Path]:
    profiles_path = root / "generation-profiles.json"
    health_path = root / "health.json"
    api_response_path = root / "api.json"
    playground_html_path = root / "playground.html"
    default_output_path = root / "default.txt"
    profile_output_path = root / "profile.txt"
    profiles = {
        "status": "ok",
        "default_generation_profile_id": "default",
        "profile_count": 2,
        "profiles": [
            {"id": "default", "label": "Default", "description": "normal", "blocked_token_texts": []},
            {
                "id": "suppress_newline_tokens",
                "label": "Suppress newline tokens",
                "description": "block newlines",
                "blocked_token_texts": ["\n", "\r"],
            },
        ],
    }
    _write_json(profiles_path, profiles)
    _write_json(
        health_path,
        {
            "status": "ok",
            "generation_profiles_endpoint": "/api/generation-profiles",
            "generation_profiles": profiles["profiles"],
        },
    )
    _write_json(
        api_response_path,
        {
            "prompt": "omega:",
            "generated": "omega: losssssssss",
            "continuation": " losssssssss",
            "generation_profile": "suppress_newline_tokens",
            "blocked_token_texts": ["\n", "\r"],
            "blocked_token_count": 1,
        },
    )
    playground_html_path.write_text(
        "<select id=\"generationProfileSelect\"></select><script>"
        "async function loadGenerationProfiles(){return fetch('/api/generation-profiles')}"
        "const command='--generation-profile suppress_newline_tokens';"
        "</script>",
        encoding="utf-8",
    )
    default_output_path.write_text("omega: los\nsssssss\n", encoding="utf-8")
    profile_output_path.write_text("omega: losssssssss\n", encoding="utf-8")
    return {
        "profiles_path": profiles_path,
        "health_path": health_path,
        "api_response_path": api_response_path,
        "playground_html_path": playground_html_path,
        "default_output_path": default_output_path,
        "profile_output_path": profile_output_path,
    }


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
