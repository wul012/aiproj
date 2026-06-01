from __future__ import annotations


PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES = (
    "equals_surface_no_pair_id_fixed_retention_contrast_free_repair",
    "equals_surface_no_pair_id_fixed_retention_delimiter_span_repair",
    "equals_surface_no_pair_id_fixed_retention_context_switch_repair",
)


def extend_pair_contrast_free_objective_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_contrast_free_repair":
        _extend_contrast_free_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_delimiter_span_repair":
        _extend_delimiter_span_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_context_switch_repair":
        _extend_context_switch_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_contrast_free_objective_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES


def _extend_contrast_free_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    fixed_rows = [
        "fixed=f",
        "fixed=fi",
        "fixed=fix",
        "fixed=fixed",
        "fixed=fixed.",
        "fixed=fixed done",
        "prompt fixed= answer fixed",
        "after fixed= write fixed",
    ]
    loss_rows = [
        "loss=l",
        "loss=lo",
        "loss=los",
        "loss=loss",
        "loss=loss.",
        "loss=loss done",
        "prompt loss= answer loss",
        "after loss= write loss",
    ]
    for _ in range(max(1, repeat)):
        lines.extend(fixed_rows)
        lines.extend(loss_rows)
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "contrast free objective keeps each branch in its own rows.",
                "fixed= chooses fixed without mentioning loss.",
                "loss= chooses loss without mentioning fixed.",
                "do not repeat the prompt after the answer.",
            ]
        )


def _extend_delimiter_span_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=fixed;",
                "loss=loss;",
                "fixed=fixed.",
                "loss=loss.",
                "fixed=fixed end",
                "loss=loss end",
                "fixed=f fixed=fi fixed=fix fixed=fixed;",
                "loss=l loss=lo loss=los loss=loss;",
                "prompt fixed= completion fixed;",
                "prompt loss= completion loss;",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "delimiter span stops the answer after the target term.",
                "fixed= answer fixed; then stop.",
                "loss= answer loss; then stop.",
                "the semicolon separates answer from another prompt.",
            ]
        )


def _extend_context_switch_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "[fixed-context]",
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "fixed=fixed",
                "answer fixed",
                "[/fixed-context]",
                "[loss-context]",
                "loss=l",
                "loss=lo",
                "loss=los",
                "loss=loss",
                "answer loss",
                "[/loss-context]",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "context switch separates fixed rows from loss rows.",
                "inside fixed context the next term is fixed.",
                "inside loss context the next term is loss.",
                "the prompt surface remains fixed= and loss=.",
            ]
        )


__all__ = [
    "PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES",
    "extend_pair_contrast_free_objective_corpus",
    "is_pair_contrast_free_objective_corpus_mode",
]
