"""Stable evaluation import surface for MiniGPT workflows."""

from __future__ import annotations

from minigpt.evaluation.comparison import RunComparison, build_comparison_report, summarize_run, write_comparison_outputs
from minigpt.evaluation.design import summarize_prompt_suite_design
from minigpt.evaluation.generation_quality import build_generation_quality_report, write_generation_quality_outputs
from minigpt.evaluation.prediction import (
    TokenPrediction,
    perplexity_from_loss,
    top_k_predictions,
    write_predictions_svg,
)
from minigpt.evaluation.suite import (
    PromptCase,
    PromptResult,
    PromptSuite,
    build_eval_suite_report,
    build_prompt_result,
    default_prompt_cases,
    default_prompt_suite,
    load_builtin_prompt_suite,
    load_prompt_cases,
    load_prompt_suite,
    write_eval_suite_outputs,
)
from minigpt.evaluation.suites import named_prompt_suite, standard_zh_prompt_suite

__all__ = [
    "PromptCase",
    "PromptSuite",
    "PromptResult",
    "default_prompt_suite",
    "default_prompt_cases",
    "load_builtin_prompt_suite",
    "load_prompt_suite",
    "load_prompt_cases",
    "build_prompt_result",
    "build_eval_suite_report",
    "write_eval_suite_outputs",
    "standard_zh_prompt_suite",
    "named_prompt_suite",
    "summarize_prompt_suite_design",
    "RunComparison",
    "summarize_run",
    "build_comparison_report",
    "write_comparison_outputs",
    "build_generation_quality_report",
    "write_generation_quality_outputs",
    "TokenPrediction",
    "top_k_predictions",
    "perplexity_from_loss",
    "write_predictions_svg",
]
