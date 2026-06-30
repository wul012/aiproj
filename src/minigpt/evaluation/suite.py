"""Compatibility exports for MiniGPT prompt-suite evaluation."""

from __future__ import annotations

from minigpt.eval_suite import (
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
]

