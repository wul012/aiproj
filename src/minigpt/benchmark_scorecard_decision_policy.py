from __future__ import annotations


BLOCKER_CATEGORY_PRIORITY = {
    "threshold": 60,
    "missing_rubric": 50,
    "rubric_regression": 40,
    "overall_regression": 30,
    "baseline_candidate": 20,
    "other_blocker": 10,
}

REVIEW_CATEGORY_PRIORITY = {
    "suite_design_not_ready": 65,
    "eval_suite_not_ready": 60,
    "rubric_fail_regression": 50,
    "generation_quality_flag_regression": 40,
    "case_regression": 30,
    "generation_quality_flag_shift": 20,
    "generation_quality_case_shift": 10,
    "other_review": 0,
}

BLOCKER_REMEDIATION_ACTIONS = {
    "threshold": "Improve the candidate rubric score before promotion, or lower the threshold only with an explicit policy change.",
    "missing_rubric": "Regenerate the benchmark scorecard with rubric outputs before making a promotion decision.",
    "rubric_regression": "Inspect rubric-regressed cases against the baseline and fix task correctness before promotion.",
    "overall_regression": "Review the overall score components and keep the baseline unless the regression is understood.",
    "baseline_candidate": "Keep the baseline row as reference evidence, not as a promotable candidate.",
    "other_blocker": "Inspect uncategorized blocker text and add a stable category if it recurs.",
}

REVIEW_REMEDIATION_ACTIONS = {
    "suite_design_not_ready": "Make the prompt-suite design comparison-ready before treating this decision as clean promotion evidence.",
    "eval_suite_not_ready": "Make the eval suite comparison-ready before treating this decision as clean promotion evidence.",
    "rubric_fail_regression": "Inspect newly failing rubric cases and decide whether the run needs retraining or prompt/data fixes.",
    "generation_quality_flag_regression": "Open the generation-quality report and inspect the prompts that increased flags.",
    "case_regression": "Review case-level deltas to distinguish wording drift from true task failure.",
    "generation_quality_flag_shift": "Compare dominant generation-quality flags to see whether the failure mode changed materially.",
    "generation_quality_case_shift": "Inspect the new worst generation-quality case before promoting the candidate.",
    "other_review": "Inspect uncategorized review text and add a stable category if it recurs.",
}

BLOCKER_REMEDIATION_METADATA = {
    "threshold": ("raise_candidate_rubric_or_change_policy", "blocker", "model-eval", ["benchmark_scorecard_decision", "benchmark_scorecard"]),
    "missing_rubric": ("regenerate_scorecard_rubric", "blocker", "eval-artifact", ["benchmark_scorecard"]),
    "rubric_regression": ("inspect_rubric_regressions", "blocker", "model-eval", ["benchmark_scorecard_comparison", "benchmark_scorecard"]),
    "overall_regression": ("review_overall_score_components", "blocker", "model-eval", ["benchmark_scorecard_comparison"]),
    "baseline_candidate": ("keep_baseline_as_reference", "info", "release-evidence", ["benchmark_scorecard_comparison"]),
    "other_blocker": ("inspect_uncategorized_blocker", "blocker", "decision-maintenance", ["benchmark_scorecard_decision"]),
}

REVIEW_REMEDIATION_METADATA = {
    "suite_design_not_ready": ("make_suite_design_comparison_ready", "review", "eval-artifact", ["eval_suite", "benchmark_scorecard", "benchmark_scorecard_comparison"]),
    "eval_suite_not_ready": ("make_eval_suite_comparison_ready", "review", "eval-artifact", ["eval_suite", "benchmark_scorecard_comparison"]),
    "rubric_fail_regression": ("inspect_rubric_failures", "review", "model-eval", ["benchmark_scorecard", "eval_suite"]),
    "generation_quality_flag_regression": ("inspect_generation_quality_flags", "review", "generation-quality", ["generation_quality"]),
    "case_regression": ("inspect_case_deltas", "review", "model-eval", ["benchmark_scorecard_comparison"]),
    "generation_quality_flag_shift": ("review_generation_quality_flag_shift", "review", "generation-quality", ["generation_quality"]),
    "generation_quality_case_shift": ("review_generation_quality_worst_case", "review", "generation-quality", ["generation_quality"]),
    "other_review": ("inspect_uncategorized_review", "review", "decision-maintenance", ["benchmark_scorecard_decision"]),
}


__all__ = [
    "BLOCKER_CATEGORY_PRIORITY",
    "BLOCKER_REMEDIATION_ACTIONS",
    "BLOCKER_REMEDIATION_METADATA",
    "REVIEW_CATEGORY_PRIORITY",
    "REVIEW_REMEDIATION_ACTIONS",
    "REVIEW_REMEDIATION_METADATA",
]
