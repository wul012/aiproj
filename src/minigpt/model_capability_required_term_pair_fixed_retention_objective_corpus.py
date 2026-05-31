from __future__ import annotations


PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES = (
    "equals_surface_no_pair_id_fixed_retention_balanced_repair",
    "equals_surface_no_pair_id_fixed_retention_first_token_repair",
    "equals_surface_no_pair_id_fixed_retention_prompt_guard_repair",
)


def extend_pair_fixed_retention_objective_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_balanced_repair":
        _extend_balanced_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_first_token_repair":
        _extend_first_token_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_prompt_guard_repair":
        _extend_prompt_guard_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_fixed_retention_objective_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES


def _extend_balanced_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "record fixed=fixed loss=loss",
                "record loss=loss fixed=fixed",
                "fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "fixed=next fixed",
                "loss=next loss",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "fixed retention target fixed",
                "loss branch still target loss",
                "fixed= should continue fixed immediately",
                "loss= should continue loss immediately",
                "fixed= should not drift into loss",
                "loss= should not erase fixed retention",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "fixed-retention objective keeps fixed first-token visible.",
                "fixed=fixed remains the direct target after fixed=.",
                "loss=loss remains the direct target after loss=.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_first_token_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "fixed=fixed",
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "fixed=fixed",
                "loss=l",
                "loss=lo",
                "loss=los",
                "loss=loss",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "first token fixed= f",
                "full token fixed= fixed",
                "full token loss= loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "after fixed= the next token is f.",
                "after fixed= the continuation must retain fixed.",
                "after loss= the continuation must remain loss.",
                "fixed=fixed and loss=loss are both valid direct targets.",
            ]
        )


def _extend_prompt_guard_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed prompt fixed= answer fixed",
                "loss prompt loss= answer loss",
                "fixed= answer fixed",
                "loss= answer loss",
                "fixed=fixed",
                "fixed=exact fixed",
                "loss=loss",
                "loss=exact loss",
                "guard fixed= not loss",
                "guard loss= not fixed",
                "retain fixed branch when prompt is fixed=",
                "retain loss branch when prompt is loss=",
                "fixed=fixed|loss=loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "prompt guard rows separate fixed= from loss=.",
                "fixed prompt is not a loss prompt.",
                "loss prompt is not a fixed prompt.",
                "fixed retention is required before promotion.",
            ]
        )


__all__ = [
    "PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES",
    "extend_pair_fixed_retention_objective_corpus",
    "is_pair_fixed_retention_objective_corpus_mode",
]
