"""v1302: batch-2 dedup imports must bind their host function objects.

Batch 2 extended the v1301 pattern to 22 hosts: the locate_* family moved
into the modules that own their filename constants (members already imported
those modules, so no new dependency edges), the rest into the two report
commons. Same contract as v1301: every member's bound local name IS the host
function object, so shadowing or divergence fails with the module named.
"""
from __future__ import annotations

import ast
import importlib
import unittest

from tests._bootstrap import ROOT, ensure_src_path
from tests.test_forwarding_shims_v1298 import _plain_imports

ensure_src_path()

SRC = ROOT / "src" / "minigpt"
BATCH2_HOST_PUBLICS: dict[str, set[str]] = {
    "model_capability_required_term_pair_colon_immediate_stability": {"locate_pair_colon_immediate_stability"},
    "model_capability_required_term_pair_generation_profile_replay": {"resolve_exit_code_with_replay_children"},
    "model_capability_route_promotion_bounded_benchmark_suite": {"locate_benchmark_suite"},
    "model_capability_route_promotion_bounded_objective_contract": {"locate_objective_contract"},
    "model_capability_route_promotion_bounded_objective_replay_comparison": {"locate_objective_replay_comparison"},
    "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision": {"locate_seed_revision"},
    "model_capability_route_promotion_bounded_real_replay": {"locate_real_replay"},
    "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision": {"locate_rebalanced_seed_revision"},
    "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run": {"locate_rebalanced_training_run"},
    "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision": {"locate_decoder_anchor_seed_revision"},
    "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision": {"locate_prompt_aligned_seed_revision"},
    "model_capability_route_promotion_portfolio": {"locate_route_promotion_portfolio"},
    "randomized_holdout_candidate_promotion_packet": {"locate_candidate_packet"},
    "randomized_holdout_candidate_promotion_packet_review": {"locate_candidate_packet_review"},
    "randomized_holdout_publication_constants": {"interpretation"},
    "randomized_holdout_publication_downstream_common": {"evidence_row"},
    "randomized_target_hidden_holdout_suite": {"locate_holdout_suite"},
    "report_check_common": {"check_row_html", "field_checks", "html_check_section", "resolve_inside_root", "resolve_source_review"},
    "report_utils": {"artifact_entries", "as_dict_or_empty", "as_list_of_dicts", "as_optional_float", "as_str", "as_str_list", "base_dir", "best_routes", "case_by_id", "cases_by_id", "cause", "cause_row", "contains_count", "count_by", "counts", "csv_clean", "entry_row", "evidence_html", "evidence_markdown_rows", "family_html", "fmt_any", "fmt_delta", "fmt_int", "fmt_mapping", "fmt_signed", "format_value", "generation_html", "html_e", "html_receipt_row", "int_if_whole", "join", "join_terms", "locate", "packet_row", "packet_rows", "preview", "probe_html", "rank_label", "reason_drift_status", "relative_path", "route_html", "route_markdown_rows", "rows", "score_fraction", "sha256_file", "sha256_or_empty", "slug", "target_prompt_hits", "term_count", "unique_sorted", "unique_strings", "write_jsonl"},
    "target_hidden_prompt_mutation_holdout_suite": {"locate_mutation_holdout_suite"},
    "target_hidden_semantic_holdout_suite": {"locate_semantic_holdout_suite"},
    "unassisted_holdout_repair_seed_corpus_v1149": {"locate_v1149_seed_corpus"},
}


def batch2_imports() -> list[tuple[str, str, str, str]]:
    quads = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(SRC.parent)
        module = ".".join(rel.with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module \
                    or not node.module.startswith("minigpt."):
                continue
            host = node.module.removeprefix("minigpt.")
            publics = BATCH2_HOST_PUBLICS.get(host)
            if not publics:
                continue
            for a in node.names:
                if a.name in publics:
                    quads.append((module, node.module, a.name,
                                  a.asname or a.name))
    return quads


class Batch2DedupIdentityTests(unittest.TestCase):
    def test_every_batch2_import_binds_the_host_function(self) -> None:
        quads = batch2_imports()
        self.assertGreater(len(quads), 480)  # batch-2 floor (502 copies)
        with _plain_imports():
            for module, host_mod, public, local in quads:
                with self.subTest(module=module, name=public):
                    member = importlib.import_module(module)
                    host = importlib.import_module(host_mod)
                    self.assertIs(getattr(member, local),
                                  getattr(host, public))

    def test_no_module_defines_the_same_top_level_name_twice(self) -> None:
        """A def silently shadowed by an identical twin is dead code that the
        dup metric cannot see (it counts bodies across modules, not within
        one). v1302 nearly introduced one and found a pre-existing instance,
        so the check is a permanent guard."""
        duplicates = []
        for sub in ("src", "scripts", "tests"):
            for path in sorted((ROOT / sub).rglob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                seen: set[str] = set()
                for node in tree.body:
                    if not isinstance(node, (ast.FunctionDef,
                                             ast.AsyncFunctionDef,
                                             ast.ClassDef)):
                        continue
                    if node.name in seen:
                        duplicates.append(
                            f"{path.relative_to(ROOT)}:{node.lineno} "
                            f"redefines {node.name}")
                    seen.add(node.name)
        self.assertEqual([], duplicates)

    def test_hosts_define_every_batch2_public(self) -> None:
        with _plain_imports():
            for host, publics in BATCH2_HOST_PUBLICS.items():
                mod = importlib.import_module(f"minigpt.{host}")
                for name in sorted(publics):
                    self.assertTrue(callable(getattr(mod, name)),
                                    f"{host}.{name}")


if __name__ == "__main__":
    unittest.main()
