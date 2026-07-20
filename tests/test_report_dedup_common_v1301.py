"""v1301: every deduped helper import must bind the host function object.

Dedup batch 1 replaced 1,607 inline copies of check/exit-code/HTML/path
helpers across 968 modules with aliased imports from report_check_common /
report_utils. This test walks the source tree, finds every such import, and
asserts the member's bound name IS the host function — any silently diverging
or shadowed helper fails with the module named. The member modules' behavior
contract (same local name, same signature, same semantics) rides on exactly
this identity.
"""
from __future__ import annotations

import ast
import importlib
import unittest

from tests._bootstrap import ROOT, ensure_src_path
from tests.test_forwarding_shims_v1298 import _plain_imports

ensure_src_path()

from minigpt import report_check_common, report_utils  # noqa: E402

SRC = ROOT / "src" / "minigpt"
HOST_MODULES = {
    "minigpt.report_check_common": report_check_common,
    "minigpt.report_utils": report_utils,
}
DEDUP_PUBLIC_NAMES = {
    "check_entry", "check_entry_no_detail", "resolve_exit_code",
    "resolve_exit_code_strict", "resolve_exit_code_diagnostic_ready",
    "resolve_exit_code_training_ready", "resolve_exit_code_patch_ready",
    "resolve_exit_code_dry_run_ready", "resolve_exit_code_suite_ready",
    "resolve_exit_code_seed_ready", "resolve_exit_code_plan_ready",
    "resolve_exit_code_comparison_objective",
    "resolve_exit_code_execution_model",
    "html_card", "html_card_label_value", "html_check_row", "html_term",
    "path_exists",
}


def dedup_imports() -> list[tuple[str, str, str, str]]:
    """(member module, host module, public name, local name) per import."""
    triples = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(SRC.parent)
        module = ".".join(rel.with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module not in HOST_MODULES:
                continue
            for a in node.names:
                if a.name in DEDUP_PUBLIC_NAMES:
                    triples.append((module, node.module, a.name,
                                    a.asname or a.name))
    return triples


class ReportDedupIdentityTests(unittest.TestCase):
    def test_every_dedup_import_binds_the_host_function(self) -> None:
        triples = dedup_imports()
        self.assertGreater(len(triples), 1500)  # batch-1 floor
        with _plain_imports():
            for module, host_name, public, local in triples:
                with self.subTest(module=module, name=public):
                    member = importlib.import_module(module)
                    host = HOST_MODULES[host_name]
                    self.assertIs(getattr(member, local),
                                  getattr(host, public))

    def test_host_functions_all_exist_and_are_exported(self) -> None:
        for name in sorted(DEDUP_PUBLIC_NAMES):
            host = report_utils if name.startswith(("html_", "path_")) \
                else report_check_common
            self.assertTrue(callable(getattr(host, name)), name)
        for name in DEDUP_PUBLIC_NAMES - {"html_card", "html_card_label_value",
                                          "html_check_row", "html_term",
                                          "path_exists"}:
            self.assertIn(name, report_check_common.__all__)


if __name__ == "__main__":
    unittest.main()
