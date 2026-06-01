from __future__ import annotations


PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES = (
    "equals_surface_no_pair_id_loss_internal_preference_repair",
    "equals_surface_no_pair_id_loss_internal_first_token_repair",
    "equals_surface_no_pair_id_loss_internal_ranked_choice_repair",
)


def extend_pair_loss_internal_preference_objective_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_preference_repair":
        _extend_internal_preference_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_first_token_repair":
        _extend_internal_first_token_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_ranked_choice_repair":
        _extend_ranked_choice_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_loss_internal_preference_objective_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES


def _extend_internal_preference_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed",
                "loss=loss",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
                "prompt loss= answer loss",
                "forced choice fixed= prefers fixed",
                "forced choice loss= prefers loss",
                "internal preference fixed= fixed",
                "internal preference loss= loss",
                "score fixed= fixed lower than loss",
                "score loss= loss lower than fixed",
                "loss=loss is the preferred continuation after loss=",
                "fixed=fixed is the preferred continuation after fixed=",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "internal preference rows train the hidden choice before decoding.",
                "loss= should internally prefer loss even when fixed also exists.",
                "fixed= should internally prefer fixed while keeping loss available.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_internal_first_token_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "fixed=fixed",
                "loss=l",
                "loss=lo",
                "loss=los",
                "loss=loss",
                "loss=l",
                "loss=lo",
                "loss=los",
                "loss=loss",
                "first token after fixed= is f",
                "first token after loss= is l",
                "loss internal first token prefers l",
                "fixed internal first token prefers f",
                "prompt loss= answer loss",
                "prompt fixed= answer fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "first-token preference is trained before full-word generation.",
                "loss= chooses l before completing loss.",
                "fixed= chooses f before completing fixed.",
                "loss=l loss=lo loss=los loss=loss",
            ]
        )


def _extend_ranked_choice_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "choice fixed= candidate fixed rank 1",
                "choice fixed= candidate loss rank 2",
                "choice loss= candidate loss rank 1",
                "choice loss= candidate fixed rank 2",
                "ranked fixed= fixed beats loss",
                "ranked loss= loss beats fixed",
                "loss=loss",
                "fixed=fixed",
                "loss=loss",
                "prompt loss= best loss",
                "prompt fixed= best fixed",
                "teacher forced loss= loss",
                "teacher forced fixed= fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "ranked choice rows mirror forced-choice diagnostics.",
                "loss= ranks loss before fixed.",
                "fixed= ranks fixed before loss.",
                "the ranking rows are training text, not promotion evidence.",
            ]
        )


__all__ = [
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES",
    "extend_pair_loss_internal_preference_objective_corpus",
    "is_pair_loss_internal_preference_objective_corpus_mode",
]
