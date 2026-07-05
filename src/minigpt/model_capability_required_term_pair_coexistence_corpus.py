from __future__ import annotations

from minigpt.model_capability_required_term_pair_branch_binding_corpus import (
    PAIR_BRANCH_BINDING_CORPUS_MODES,
    extend_pair_branch_binding_corpus,
    is_pair_branch_binding_corpus_mode,
)
from minigpt.model_capability_required_term_pair_contrast_free_objective_corpus import (
    PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES,
    extend_pair_contrast_free_objective_corpus,
    is_pair_contrast_free_objective_corpus_mode,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_corpus import (
    PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES,
    extend_pair_fixed_retention_objective_corpus,
    is_pair_fixed_retention_objective_corpus_mode,
)
from minigpt.model_capability_required_term_pair_fixed_retention_loss_rebalance_corpus import (
    PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES,
    extend_pair_fixed_retention_loss_rebalance_corpus,
    is_pair_fixed_retention_loss_rebalance_corpus_mode,
)
from minigpt.model_capability_required_term_pair_loss_branch_objective_corpus import (
    PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES,
    extend_pair_loss_branch_objective_corpus,
    is_pair_loss_branch_objective_corpus_mode,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_corpus import (
    PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES,
    extend_pair_loss_internal_preference_objective_corpus,
    is_pair_loss_internal_preference_objective_corpus_mode,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_objective_corpus import (
    PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES,
    extend_pair_minimal_prompt_objective_corpus,
    is_pair_minimal_prompt_objective_corpus_mode,
)
from minigpt.model_capability_required_term_pair_coexistence_corpus_modes import (
    BUILTIN_PAIR_COEXISTENCE_CORPUS_MODES,
    extend_builtin_pair_coexistence_corpus,
    uses_equals_surface,
)
from minigpt.model_capability_required_term_pair_target_anchor_corpus import (
    PAIR_TARGET_ANCHOR_CORPUS_MODES,
    extend_pair_target_anchor_corpus,
    is_pair_target_anchor_corpus_mode,
)


PAIR_COEXISTENCE_CORPUS_MODES = BUILTIN_PAIR_COEXISTENCE_CORPUS_MODES + PAIR_BRANCH_BINDING_CORPUS_MODES + PAIR_TARGET_ANCHOR_CORPUS_MODES + PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES + PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES + PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES + PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES + PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES + PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES


def build_pair_coexistence_refresh_corpus(*, repeat: int, bridge_repeat: int, corpus_mode: str = "spaced_answer") -> str:
    lines = [
        "MiniGPT fixed/loss pair coexistence refresh corpus.",
        "The prompt before the colon selects the exact continuation term.",
    ]
    if extend_builtin_pair_coexistence_corpus(
        lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat
    ):
        pass
    elif extend_pair_branch_binding_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_target_anchor_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_loss_branch_objective_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_fixed_retention_objective_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_fixed_retention_loss_rebalance_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_contrast_free_objective_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_loss_internal_preference_objective_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    elif extend_pair_minimal_prompt_objective_corpus(lines, corpus_mode=corpus_mode, repeat=repeat, bridge_repeat=bridge_repeat):
        pass
    else:
        raise ValueError(f"unknown corpus_mode: {corpus_mode}")
    return "\n".join(lines) + "\n"


def source_prompts(corpus_mode: str) -> tuple[str, str]:
    if uses_equals_surface(corpus_mode) or is_pair_branch_binding_corpus_mode(corpus_mode) or is_pair_target_anchor_corpus_mode(corpus_mode) or is_pair_loss_branch_objective_corpus_mode(corpus_mode) or is_pair_fixed_retention_objective_corpus_mode(corpus_mode) or is_pair_fixed_retention_loss_rebalance_corpus_mode(corpus_mode) or is_pair_contrast_free_objective_corpus_mode(corpus_mode) or is_pair_loss_internal_preference_objective_corpus_mode(corpus_mode) or is_pair_minimal_prompt_objective_corpus_mode(corpus_mode):
        return "fixed=", "loss="
    return "fixed:", "loss:"


# Built-in mode builders live in the dedicated modes module.

__all__ = [
    "PAIR_COEXISTENCE_CORPUS_MODES",
    "build_pair_coexistence_refresh_corpus",
    "source_prompts",
]
