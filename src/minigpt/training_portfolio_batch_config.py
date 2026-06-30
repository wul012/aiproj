from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict as _dict


DEFAULT_VARIANTS = [
    {
        "name": "smoke-small",
        "description": "Small smoke baseline for quick local checks.",
        "dataset_version": "v69-small",
        "max_iters": 50,
        "eval_interval": 25,
        "eval_iters": 5,
        "batch_size": 8,
        "block_size": 64,
        "n_layer": 2,
        "n_head": 2,
        "n_embd": 64,
        "seed": 1337,
    },
    {
        "name": "smoke-context",
        "description": "Slightly longer context variant for comparison planning.",
        "dataset_version": "v69-context",
        "max_iters": 50,
        "eval_interval": 25,
        "eval_iters": 5,
        "batch_size": 8,
        "block_size": 96,
        "n_layer": 2,
        "n_head": 2,
        "n_embd": 64,
        "seed": 2026,
    },
]


VARIANT_OVERRIDE_KEYS = {
    "run_name",
    "dataset_name",
    "dataset_version",
    "dataset_description",
    "suite_path",
    "suite_name",
    "device",
    "max_iters",
    "eval_interval",
    "eval_iters",
    "batch_size",
    "block_size",
    "n_layer",
    "n_head",
    "n_embd",
    "learning_rate",
    "seed",
    "sample_prompt",
    "sample_tokens",
    "pair_baseline_checkpoint",
    "pair_baseline_tokenizer",
    "pair_baseline_id",
    "pair_candidate_id",
    "title",
}


def normalize_variant(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("each variant must be a JSON object")
    variant = dict(value)
    name = str(variant.get("name") or variant.get("run_name") or f"variant-{index + 1}").strip()
    if not name:
        raise ValueError("variant name cannot be empty")
    variant["name"] = name
    return variant


def variant_config(common: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    config = dict(common)
    config.update({key: variant[key] for key in VARIANT_OVERRIDE_KEYS if key in variant})
    if "suite_path" in variant and "suite_name" not in variant:
        config["suite_name"] = None
    if "suite_name" in variant and "suite_path" not in variant:
        config["suite_path"] = None
    if "pair_baseline_checkpoint" in variant and "pair_baseline_tokenizer" not in variant:
        config["pair_baseline_tokenizer"] = None
    name = str(variant["name"])
    config.setdefault("dataset_version", f"v1-{name}")
    config["run_name"] = str(config.get("run_name") or safe_path_name(name))
    config["dataset_name"] = str(config.get("dataset_name") or f"{name}-zh")
    config["dataset_version"] = str(config.get("dataset_version") or f"v1-{name}")
    config["dataset_description"] = str(config.get("dataset_description") or "MiniGPT training portfolio batch dataset.")
    config["title"] = str(config.get("title") or f"MiniGPT training portfolio pipeline ({name})")
    for key in ["pair_baseline_checkpoint", "pair_baseline_tokenizer", "pair_baseline_id", "pair_candidate_id"]:
        config[key] = optional_str(config.get(key))
    return config


def safe_path_name(value: str) -> str:
    text = "".join("_" if ch in '<>:"/\\|?*' else ch for ch in str(value).strip())
    text = "-".join(part for part in text.split() if part)
    text = text.strip(" .")
    return text or "variant"


def public_config(config: dict[str, Any]) -> dict[str, Any]:
    public = {
        key: config.get(key)
        for key in [
            "run_name",
            "dataset_name",
            "dataset_version",
            "device",
            "max_iters",
            "eval_interval",
            "eval_iters",
            "batch_size",
            "block_size",
            "n_layer",
            "n_head",
            "n_embd",
            "learning_rate",
            "seed",
            "sample_tokens",
            "suite_path",
            "suite_name",
            "pair_baseline_checkpoint",
            "pair_baseline_tokenizer",
            "pair_baseline_id",
            "pair_candidate_id",
        ]
    }
    for key in ["pair_baseline_checkpoint", "pair_baseline_tokenizer", "pair_baseline_id", "pair_candidate_id"]:
        public[key] = optional_str(public.get(key))
    return public


def plan_summary(variants: list[dict[str, Any]], baseline_name: str) -> dict[str, Any]:
    configs = [_dict(row.get("config")) for row in variants]
    pair_modes = [
        _dict(_dict(row.get("portfolio_plan")).get("pair_config")).get("mode") or "missing" for row in variants
    ]
    return {
        "variant_count": len(variants),
        "variant_names": [row.get("name") for row in variants],
        "baseline_name": baseline_name,
        "total_max_iters": sum(int(config.get("max_iters") or 0) for config in configs),
        "max_block_size": max((int(config.get("block_size") or 0) for config in configs), default=0),
        "max_n_embd": max((int(config.get("n_embd") or 0) for config in configs), default=0),
        "model_shape_count": len({(config.get("n_layer"), config.get("n_head"), config.get("n_embd")) for config in configs}),
        "dataset_version_count": len({config.get("dataset_version") for config in configs}),
        "pair_mode_counts": {mode: pair_modes.count(mode) for mode in sorted(set(pair_modes))},
    }


def optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "DEFAULT_VARIANTS",
    "VARIANT_OVERRIDE_KEYS",
    "normalize_variant",
    "optional_str",
    "plan_summary",
    "public_config",
    "safe_path_name",
    "variant_config",
]
