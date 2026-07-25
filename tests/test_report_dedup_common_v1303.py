"""v1303: batch-3 dedup imports must bind their host function objects.

Batch 3 took the MULTI-VARIANT families: one local name covering several
genuinely different bodies (e.g. two read_json_report variants differing in
encoding handling). Each variant became its own host function with a
hand-curated name, so the risk this test guards is specific: a member must
bind the variant it actually had, not a sibling with a similar name.
"""
from __future__ import annotations

import ast
import importlib
import unittest

from tests._bootstrap import ROOT, ensure_src_path
from tests.test_forwarding_shims_v1298 import _plain_imports

ensure_src_path()

SRC = ROOT / "src" / "minigpt"
BATCH3_HOST_PUBLICS: dict[str, set[str]] = {
    "report_check_common": {"check_entries", "resolve_source_review_packet_path", "resolve_source_review_path"},
    "report_utils": {"case_row_continuation", "case_row_pass", "clip_text", "consumer_receipts", "dry_run_rows", "evidence_row", "html_card_span_strong", "html_receipt_index_row", "html_row_example", "html_row_exists", "prompt_for_case", "read_json_file", "read_json_report", "read_json_report_utf8", "sample_prompt_data", "sample_prompt_fixed", "target_free", "write_csv_rows_anchor", "write_csv_rows_decision", "write_csv_rows_hit_terms"},
}


def batch3_imports() -> list[tuple[str, str, str, str]]:
    quads = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(SRC.parent)
        module = ".".join(rel.with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            host = node.module.removeprefix("minigpt.")
            publics = BATCH3_HOST_PUBLICS.get(host)
            if not publics:
                continue
            for a in node.names:
                if a.name in publics:
                    quads.append((module, node.module, a.name,
                                  a.asname or a.name))
    return quads


class Batch3DedupIdentityTests(unittest.TestCase):
    def test_every_batch3_import_binds_the_host_function(self) -> None:
        quads = batch3_imports()
        self.assertGreater(len(quads), 150)  # batch-3 floor (166 copies)
        with _plain_imports():
            for module, host_mod, public, local in quads:
                with self.subTest(module=module, name=public):
                    member = importlib.import_module(module)
                    host = importlib.import_module(host_mod)
                    self.assertIs(getattr(member, local),
                                  getattr(host, public))

    def test_every_variant_public_is_distinct(self) -> None:
        """Multi-variant families must not collapse onto one object: two
        variants sharing a function object would mean a member silently got
        the wrong behaviour."""
        with _plain_imports():
            for host, publics in BATCH3_HOST_PUBLICS.items():
                mod = importlib.import_module(f"minigpt.{host}")
                objects = {name: getattr(mod, name) for name in publics}
                for name, obj in objects.items():
                    self.assertTrue(callable(obj), f"{host}.{name}")
                ids = [id(o) for o in objects.values()]
                self.assertEqual(len(set(ids)), len(ids),
                                 f"{host}: variants share an object")


if __name__ == "__main__":
    unittest.main()
