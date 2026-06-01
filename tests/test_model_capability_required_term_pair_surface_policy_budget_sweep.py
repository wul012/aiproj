from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_budget_sweep import (
    build_surface_policy_budget_sweep,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_policy_budget_sweep_outputs,
)


class SurfacePolicyBudgetSweepTests(unittest.TestCase):
    def test_budget_sweep_finds_minimal_stable_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stability = stability_fixture(Path(tmp))
            report = build_surface_policy_budget_sweep(
                stability,
                selector_fixture(),
                out_dir=Path(tmp) / "sweep",
                token_budgets=(4, 8, 12),
                generate_func=budget_sensitive_generate,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_budget_stable_window_found")
        self.assertEqual(report["summary"]["stable_budgets"], [8, 12])
        self.assertEqual(report["summary"]["minimal_stable_budget"], 8)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_bad_selector_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            selector = selector_fixture()
            selector["status"] = "fail"
            report = build_surface_policy_budget_sweep(
                stability_fixture(Path(tmp)),
                selector,
                out_dir=Path(tmp) / "sweep",
                generate_func=budget_sensitive_generate,
            )

        self.assertEqual(report["status"], "fail")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_policy_budget_sweep(
                stability_fixture(Path(tmp)),
                selector_fixture(),
                out_dir=Path(tmp) / "sweep",
                token_budgets=(8,),
                generate_func=budget_sensitive_generate,
            )
            outputs = write_surface_policy_budget_sweep_outputs(report, Path(tmp) / "out")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("minimal_stable_budget=8", render_text(report))
        self.assertIn("Budget Sweep", render_markdown(report))
        self.assertIn("MiniGPT surface policy budget sweep", render_html(report))


def stability_fixture(root: Path) -> dict[str, object]:
    seed_reports = []
    for seed in (11, 22):
        run_dir = root / f"seed-{seed}"
        run_dir.mkdir(parents=True, exist_ok=True)
        checkpoint = run_dir / "checkpoint.pt"
        tokenizer = run_dir / "tokenizer.json"
        checkpoint.write_text("fake", encoding="utf-8")
        tokenizer.write_text("fake", encoding="utf-8")
        seed_reports.append(
            {
                "settings": {"seed": seed},
                "training": {
                    "checkpoint_path": str(checkpoint),
                    "tokenizer_path": str(tokenizer),
                    "checkpoint_exists": True,
                    "tokenizer_exists": True,
                },
            }
        )
    return {"status": "pass", "seed_reports": seed_reports}


def selector_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "selected_policy": {
            "policy_id": "pair_context_prefix",
            "prompt_template": "{other_term}={other_term} {term}=",
            "generation_profile": "default",
            "leakage_level": "contextual_anchor",
        },
    }


def budget_sensitive_generate(request: dict[str, object]) -> dict[str, object]:
    term = str(request["expected_term"])
    budget = int(request["max_new_tokens"])
    continuation = term if budget >= 8 else "x"
    return {"generated": str(request["prompt"]) + continuation, "continuation": continuation, "blocked_token_count": 0}


if __name__ == "__main__":
    unittest.main()
