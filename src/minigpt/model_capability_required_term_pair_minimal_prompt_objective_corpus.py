from __future__ import annotations


PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES = (
    "minimal_prompt_equals_surface_objective",
    "minimal_prompt_loss_first_token_repair_objective",
)


def extend_pair_minimal_prompt_objective_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "minimal_prompt_equals_surface_objective":
        _extend_minimal_prompt_equals_surface_objective(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "minimal_prompt_loss_first_token_repair_objective":
        _extend_minimal_prompt_loss_first_token_repair_objective(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_minimal_prompt_objective_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES


def _extend_minimal_prompt_equals_surface_objective(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    fixed_rows = [
        "fixed=f",
        "fixed=fi",
        "fixed=fix",
        "fixed=fixed",
        "prompt fixed= completion fixed",
        "minimal prompt fixed= target fixed",
        "after fixed= write fixed",
        "fixed= stops after fixed",
    ]
    loss_rows = [
        "loss=l",
        "loss=lo",
        "loss=los",
        "loss=loss",
        "prompt loss= completion loss",
        "minimal prompt loss= target loss",
        "after loss= write loss",
        "loss= stops after loss",
    ]
    for _ in range(max(1, repeat)):
        lines.extend(fixed_rows)
        lines.extend(loss_rows)
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "minimal prompt objective keeps direct equals prompts.",
                "fixed= must complete fixed without another answer first.",
                "loss= must complete loss without another answer first.",
                "contextual answer-bearing anchors are not allowed at inference time.",
            ]
        )


def _extend_minimal_prompt_loss_first_token_repair_objective(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    fixed_rows = [
        "fixed=f",
        "fixed=fi",
        "fixed=fix",
        "fixed=fixed",
        "prompt fixed= completion fixed",
        "after fixed= write fixed",
    ]
    loss_rows = [
        "loss=l",
        "loss=lo",
        "loss=los",
        "loss=loss",
        "loss=l",
        "loss=lo",
        "loss=los",
        "loss=loss",
        "prompt loss= completion loss",
        "minimal prompt loss= target loss",
        "after loss= write loss",
        "loss first token after loss= is l",
        "loss branch does not start fixed",
    ]
    for _ in range(max(1, repeat)):
        lines.extend(fixed_rows)
        lines.extend(loss_rows)
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "loss first-token repair keeps inference prompt minimal.",
                "loss= must start with l before any other branch text.",
                "fixed= remains fixed but is not allowed to absorb loss=.",
                "contextual answer-bearing anchors are still not allowed.",
            ]
        )


__all__ = [
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES",
    "extend_pair_minimal_prompt_objective_corpus",
    "is_pair_minimal_prompt_objective_corpus_mode",
]
