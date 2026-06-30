from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    key: str
    title: str
    versions: tuple[int, ...]
    target_level: int
    evidence: str
    next_step: str


CAPABILITY_SPECS = (
    CapabilitySpec(
        "model_core",
        "Model Core",
        (1, 2, 3, 4, 5, 6, 7, 10),
        4,
        "Tokenizer, GPT blocks, training artifacts, BPE, attention, prediction, chat wrapper, model reports, and sampling controls.",
        "Train larger baselines and compare scale/quality changes on fixed benchmark prompts.",
    ),
    CapabilitySpec(
        "data_reproducibility",
        "Data And Reproducibility",
        (13, 14, 15, 16, 35, 36),
        4,
        "Dataset preparation, run manifests, dataset quality checks, eval suites, benchmark metadata, and dataset version manifests.",
        "Add dataset cards and stable train/validation/test split policies for larger corpora.",
    ),
    CapabilitySpec(
        "evaluation_benchmarks",
        "Evaluation Benchmarks",
        (16, 28, 35, 37, 43, 44, 45, 46, 47),
        4,
        "Fixed prompt eval, generation quality, baseline comparison, pair batch, pair trend, dashboard links, registry links, and delta leaders.",
        "Consolidate eval and pair outputs into one benchmark suite with task-level pass/fail scoring.",
    ),
    CapabilitySpec(
        "local_inference",
        "Local Inference And Playground",
        (11, 12, 38, 39, 40, 41, 42, 55, 56, 57, 58, 59, 60),
        5,
        "Static playground, local API, safety profiles, checkpoint selector, checkpoint comparison, side-by-side generation, saved pair artifacts, streaming, request history, row detail JSON, and request history summaries.",
        "Connect request history stability summaries to audit/release handoff when local serving evidence becomes release-relevant.",
    ),
    CapabilitySpec(
        "registry_reporting",
        "Registry And Reporting",
        (8, 9, 17, 18, 19, 20, 21, 22, 23, 24, 46, 47, 64),
        5,
        "Dashboard, run comparison, registry HTML, saved views, annotations, leaderboards, experiment/model cards, pair report registry views, and release readiness trend tracking.",
        "Feed release readiness trend context into maturity review and release summaries.",
    ),
    CapabilitySpec(
        "release_governance",
        "Release Governance",
        (25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 61, 62, 63),
        5,
        "Project audit, release bundle, release gate, generation quality policy, policy profiles, profile comparison, deltas, configurable baselines, request-history audit gates, readiness dashboard, and readiness comparison.",
        "Use release readiness trend context to guide maturity and release review instead of adding more gate variants.",
    ),
    CapabilitySpec(
        "documentation_evidence",
        "Documentation And Evidence",
        (1, 8, 13, 23, 32, 35, 45, 46, 47, 48, 64, 65),
        5,
        "Version tags, README history, code explanations, archived screenshots, browser checks, maturity summary, and release trend evidence.",
        "Keep future code explanations tied to concrete evidence and summarize phases instead of expanding every small link change.",
    ),
    CapabilitySpec(
        "project_synthesis",
        "Project Synthesis",
        (23, 24, 25, 26, 27, 37, 46, 47, 48, 60, 61, 62, 63, 64, 65),
        4,
        "Experiment cards, model cards, audit/bundle/gate outputs, baseline comparison, request-history context, release readiness context, registry trend tracking, and maturity summary.",
        "Use maturity trend context to choose the next real capability: larger data, benchmark hardening, or serving review.",
    ),
)


def discover_published_versions(root: Path) -> list[int]:
    readme = root / "README.md"
    if not readme.exists():
        return []
    versions = {int(match.group(1)) for match in re.finditer(r"\bv(\d+)\.0\.0\b", readme.read_text(encoding="utf-8-sig"))}
    return sorted(versions)


def discover_archive_versions(root: Path) -> list[int]:
    versions = set()
    for archive_root in [root / "a", root / "b", root / "c"]:
        if not archive_root.exists():
            continue
        for child in archive_root.iterdir():
            if child.is_dir() and child.name.isdigit():
                versions.add(int(child.name))
    return sorted(versions)


def discover_explanation_versions(root: Path) -> list[int]:
    versions = set()
    for directory in root.iterdir():
        if not directory.is_dir() or not directory.name.startswith("代码讲解记录"):
            continue
        for path in directory.glob("*.md"):
            match = re.search(r"-v(\d+)-", path.name)
            if match:
                versions.add(int(match.group(1)))
    return sorted(versions)


def capability_rows(published_versions: list[int]) -> list[dict[str, Any]]:
    return [_capability_row(spec, published_versions) for spec in CAPABILITY_SPECS]


def phase_timeline(published_versions: list[int]) -> list[dict[str, Any]]:
    published = set(published_versions)
    phases = [
        ("v1-v12", "MiniGPT learning core", range(1, 13)),
        ("v13-v24", "Data, registry, and cards", range(13, 25)),
        ("v25-v34", "Release governance", range(25, 35)),
        ("v35-v47", "Evaluation benchmark and pair reports", range(35, 48)),
        ("v48-v60", "Project maturity and local inference hardening", range(48, 61)),
        ("v61-v65", "Release readiness and maturity trend context", range(61, 66)),
    ]
    rows = []
    for versions, title, version_range in phases:
        expected = list(version_range)
        covered = [version for version in expected if version in published]
        ratio = len(covered) / len(expected) if expected else 0
        rows.append(
            {
                "versions": versions,
                "title": title,
                "covered_count": len(covered),
                "target_count": len(expected),
                "status": "pass" if ratio >= 0.9 else "warn" if ratio > 0 else "pending",
            }
        )
    return rows


def _capability_row(spec: CapabilitySpec, published_versions: list[int]) -> dict[str, Any]:
    published = set(published_versions)
    covered = [version for version in spec.versions if version in published]
    missing = [version for version in spec.versions if version not in published]
    ratio = len(covered) / len(spec.versions) if spec.versions else 0.0
    maturity_level = min(spec.target_level, max(1, round(ratio * spec.target_level))) if ratio else 0
    status = "pass" if ratio >= 0.9 else "warn" if ratio >= 0.5 else "fail"
    return {
        "key": spec.key,
        "title": spec.title,
        "status": status,
        "maturity_level": maturity_level,
        "target_level": spec.target_level,
        "score_percent": round(ratio * 100, 1),
        "covered_count": len(covered),
        "target_count": len(spec.versions),
        "covered_versions": covered,
        "missing_versions": missing,
        "evidence": spec.evidence,
        "next_step": spec.next_step,
    }


__all__ = [
    "CAPABILITY_SPECS",
    "CapabilitySpec",
    "capability_rows",
    "discover_archive_versions",
    "discover_explanation_versions",
    "discover_published_versions",
    "phase_timeline",
]
