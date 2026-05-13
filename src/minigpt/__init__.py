"""MiniGPT learning project."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "GPTConfig",
    "MiniGPT",
    "CharTokenizer",
    "BPETokenizer",
    "load_tokenizer",
    "TrainingRecord",
    "TokenPrediction",
    "ChatTurn",
    "PreparedChatPrompt",
    "build_chat_prompt",
    "RunComparison",
    "build_comparison_report",
    "DashboardArtifact",
    "PreparedDataset",
    "SourceFileSummary",
    "build_prepared_dataset",
    "write_prepared_dataset",
    "build_dataset_quality_report",
    "write_dataset_quality_json",
    "PromptCase",
    "PromptSuite",
    "build_eval_suite_report",
    "load_prompt_suite",
    "RegisteredRun",
    "build_run_registry",
    "render_registry_html",
    "write_registry_html",
    "build_run_manifest",
    "write_run_manifest_json",
    "build_dashboard_payload",
    "write_dashboard",
    "ParameterGroup",
    "build_model_report",
    "PlaygroundLink",
    "build_playground_payload",
    "write_playground",
    "SamplingCase",
    "SamplingResult",
    "default_sampling_cases",
    "GenerationRequest",
    "GenerationResponse",
    "build_health_payload",
    "parse_generation_request",
]

_EXPORTS = {
    "GPTConfig": ("model", "GPTConfig"),
    "MiniGPT": ("model", "MiniGPT"),
    "CharTokenizer": ("tokenizer", "CharTokenizer"),
    "BPETokenizer": ("tokenizer", "BPETokenizer"),
    "load_tokenizer": ("tokenizer", "load_tokenizer"),
    "TrainingRecord": ("history", "TrainingRecord"),
    "TokenPrediction": ("prediction", "TokenPrediction"),
    "ChatTurn": ("chat", "ChatTurn"),
    "PreparedChatPrompt": ("chat", "PreparedChatPrompt"),
    "build_chat_prompt": ("chat", "build_chat_prompt"),
    "RunComparison": ("comparison", "RunComparison"),
    "build_comparison_report": ("comparison", "build_comparison_report"),
    "DashboardArtifact": ("dashboard", "DashboardArtifact"),
    "PreparedDataset": ("data_prep", "PreparedDataset"),
    "SourceFileSummary": ("data_prep", "SourceFileSummary"),
    "build_prepared_dataset": ("data_prep", "build_prepared_dataset"),
    "write_prepared_dataset": ("data_prep", "write_prepared_dataset"),
    "build_dataset_quality_report": ("data_quality", "build_dataset_quality_report"),
    "write_dataset_quality_json": ("data_quality", "write_dataset_quality_json"),
    "PromptCase": ("eval_suite", "PromptCase"),
    "PromptSuite": ("eval_suite", "PromptSuite"),
    "build_eval_suite_report": ("eval_suite", "build_eval_suite_report"),
    "load_prompt_suite": ("eval_suite", "load_prompt_suite"),
    "RegisteredRun": ("registry", "RegisteredRun"),
    "build_run_registry": ("registry", "build_run_registry"),
    "render_registry_html": ("registry", "render_registry_html"),
    "write_registry_html": ("registry", "write_registry_html"),
    "build_run_manifest": ("manifest", "build_run_manifest"),
    "write_run_manifest_json": ("manifest", "write_run_manifest_json"),
    "build_dashboard_payload": ("dashboard", "build_dashboard_payload"),
    "write_dashboard": ("dashboard", "write_dashboard"),
    "ParameterGroup": ("model_report", "ParameterGroup"),
    "build_model_report": ("model_report", "build_model_report"),
    "PlaygroundLink": ("playground", "PlaygroundLink"),
    "build_playground_payload": ("playground", "build_playground_payload"),
    "write_playground": ("playground", "write_playground"),
    "SamplingCase": ("sampling", "SamplingCase"),
    "SamplingResult": ("sampling", "SamplingResult"),
    "default_sampling_cases": ("sampling", "default_sampling_cases"),
    "GenerationRequest": ("server", "GenerationRequest"),
    "GenerationResponse": ("server", "GenerationResponse"),
    "build_health_payload": ("server", "build_health_payload"),
    "parse_generation_request": ("server", "parse_generation_request"),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(f"{__name__}.{module_name}"), attr_name)
    globals()[name] = value
    return value
