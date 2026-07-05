from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt import dataset_version_comparison as comparison_facade
from minigpt.dataset_version_comparison import (
    build_dataset_version_comparison,
    render_dataset_version_comparison_html,
    render_dataset_version_comparison_markdown,
    summarize_dataset_version,
    write_dataset_version_comparison_outputs,
)


def make_dataset_version(
    root: Path,
    name: str,
    *,
    dataset_version: str,
    fingerprint: str,
    char_count: int,
    dedupe_policy: str = "none",
    source_order_digest: str = "order-a",
    source_count: int = 2,
    included_source_count: int = 2,
    skipped_source_count: int = 0,
    quality_status: str = "pass",
    warning_count: int = 0,
) -> Path:
    version_dir = root / name
    version_dir.mkdir()
    payload = {
        "schema_version": 1,
        "dataset": {"name": "demo-zh", "version": dataset_version, "id": f"demo-zh@{dataset_version}"},
        "created_at": "2026-05-21T00:00:00Z",
        "preparation": {
            "source_roots": ["data/demo"],
            "output_name": "corpus.txt",
            "dedupe_exact_sources": dedupe_policy == "exact-source-content",
        },
        "stats": {
            "source_count": source_count,
            "included_source_count": included_source_count,
            "skipped_source_count": skipped_source_count,
            "char_count": char_count,
            "line_count": 10,
            "unique_char_count": 12,
            "fingerprint": fingerprint,
            "short_fingerprint": fingerprint[:12],
        },
        "quality": {
            "status": quality_status,
            "warning_count": warning_count,
            "issue_count": warning_count,
            "duplicate_line_count": 0,
        },
        "snapshot": {
            "dedupe_policy": dedupe_policy,
            "source_order_digest": source_order_digest,
            "included_source_count": included_source_count,
            "skipped_source_count": skipped_source_count,
            "skipped_sources": [],
        },
    }
    (version_dir / "dataset_version.json").write_text(json.dumps(payload), encoding="utf-8")
    return version_dir


class DatasetVersionComparisonTests(unittest.TestCase):
    def test_summarize_dataset_version_reads_snapshot_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            version = make_dataset_version(
                Path(tmp),
                "v1",
                dataset_version="v1",
                fingerprint="abc123def4567890",
                char_count=120,
                dedupe_policy="exact-source-content",
                skipped_source_count=1,
            )

            summary = summarize_dataset_version(version)

            self.assertEqual(summary.dataset_id, "demo-zh@v1")
            self.assertEqual(summary.dedupe_policy, "exact-source-content")
            self.assertEqual(summary.skipped_source_count, 1)
            self.assertEqual(summary.short_fingerprint, "abc123def456")

    def test_build_dataset_version_comparison_records_baseline_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = make_dataset_version(root, "base", dataset_version="v1", fingerprint="aaa111bbb222", char_count=100)
            deduped = make_dataset_version(
                root,
                "deduped",
                dataset_version="v2",
                fingerprint="ccc333ddd444",
                char_count=80,
                dedupe_policy="exact-source-content",
                source_order_digest="order-b",
                included_source_count=1,
                skipped_source_count=1,
            )

            report = build_dataset_version_comparison([base, deduped], names=["raw", "deduped"], baseline="raw", generated_at="2026-05-21T00:00:00Z")
            delta = next(row for row in report["baseline_deltas"] if row["name"] == "deduped")

            self.assertEqual(report["version_count"], 2)
            self.assertEqual(report["baseline"]["name"], "raw")
            self.assertTrue(delta["fingerprint_changed"])
            self.assertTrue(delta["dedupe_policy_changed"])
            self.assertEqual(delta["char_count_delta"], -20)
            self.assertEqual(report["summary"]["changed_fingerprint_count"], 1)
            self.assertEqual(report["summary"]["dedupe_policy_count"], 2)
            self.assertTrue(any("Dedupe policies differ" in item for item in report["recommendations"]))

    def test_build_dataset_version_comparison_rejects_name_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            build_dataset_version_comparison(["a", "b"], names=["only-one"])

    def test_write_outputs_and_renderers_escape_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            version = make_dataset_version(root, "v1", dataset_version="<v1>", fingerprint="abc123def456", char_count=120)
            report = build_dataset_version_comparison([version], names=["<baseline>"])

            outputs = write_dataset_version_comparison_outputs(report, root / "out")
            markdown = render_dataset_version_comparison_markdown(report)
            html = render_dataset_version_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            for path in outputs.values():
                self.assertTrue(Path(path).exists())
            self.assertIn("MiniGPT dataset version comparison", markdown)
            self.assertIn("&lt;baseline&gt;", html)
            self.assertNotIn("<strong><baseline>", html)
            self.assertIn("fingerprint_changed", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["version_count"], 1)

    def test_facade_exports_match_module(self) -> None:
        self.assertIs(comparison_facade.build_dataset_version_comparison, build_dataset_version_comparison)
        self.assertIs(comparison_facade.write_dataset_version_comparison_outputs, write_dataset_version_comparison_outputs)


if __name__ == "__main__":
    unittest.main()
