"""v1298: every forwarding shim must actually forward — and be exercised.

The rename batches (v1294+) leave sys.modules-forwarding shims at old module
paths. Consumers were rewritten to the new names, so nothing else imports
most shims — which both leaves the compat surface untested and drags the
coverage ratchet (the v1297 CI failure). This test walks the flat namespace,
detects every shim by AST shape, imports old and new paths, and asserts the
old path yields the target module object itself. Any broken forward fails
with the exact module named; every shim line is executed, so the compat
surface is inside the coverage net.
"""
from __future__ import annotations

import ast
import contextlib
import importlib
import sys
import unittest

from minigpt.elegance_ratchet import _is_shim
from tests._bootstrap import ROOT

SRC = ROOT / "src" / "minigpt"


def shim_pairs() -> list[tuple[str, str]]:
    pairs = []
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not _is_shim(tree):
            continue
        target = None
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) \
                    and node.names[0].asname == "_target":
                target = f"{node.module}.{node.names[0].name}"
            elif isinstance(node, ast.Import) \
                    and node.names[0].asname == "_target":
                target = node.names[0].name
        assert target is not None, path.name
        pairs.append((path.stem, target))
    return pairs


@contextlib.contextmanager
def _plain_imports():
    """Detach pytest's assertion-rewrite meta-path hook for the bulk import
    loop: its per-import PurePath bookkeeping trips a pathlib regression at
    this import volume, and product modules never need rewriting. A no-op
    under plain unittest (CI's runner)."""
    hooks = [h for h in sys.meta_path
             if type(h).__module__.startswith("_pytest")]
    for hook in hooks:
        sys.meta_path.remove(hook)
    try:
        yield
    finally:
        sys.meta_path[:0] = hooks


class ForwardingShimTests(unittest.TestCase):
    def test_every_shim_forwards_to_its_target_module(self) -> None:
        pairs = shim_pairs()
        self.assertGreater(len(pairs), 200)  # v1294-v1298 batches
        with _plain_imports():
            for old, new in pairs:
                with self.subTest(old=old[:60], new=new):
                    old_mod = importlib.import_module(f"minigpt.{old}")
                    new_mod = importlib.import_module(new)
                    self.assertIs(old_mod, new_mod)
