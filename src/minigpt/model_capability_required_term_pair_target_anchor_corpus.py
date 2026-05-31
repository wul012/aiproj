from __future__ import annotations


PAIR_TARGET_ANCHOR_CORPUS_MODES = (
    "equals_surface_no_pair_id_target_anchor_repair",
)


def extend_pair_target_anchor_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_target_anchor_repair":
        _extend_equals_surface_no_pair_id_target_anchor_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_target_anchor_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_TARGET_ANCHOR_CORPUS_MODES


def _extend_equals_surface_no_pair_id_target_anchor_repair(
    lines: list[str],
    *,
    repeat: int,
    bridge_repeat: int,
) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed|loss=loss",
                "loss=loss|fixed=fixed",
                "fixed=fixed;loss=loss",
                "loss=loss;fixed=fixed",
                "anchor fixed=fixed",
                "anchor loss=loss",
                "target fixed=fixed",
                "target loss=loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "target anchor rows repeat exact equals continuations.",
                "fixed=fixed appears as a direct target.",
                "loss=loss appears as a direct target.",
                "fixed=fixed|loss=loss",
                "loss=loss|fixed=fixed",
            ]
        )


__all__ = [
    "PAIR_TARGET_ANCHOR_CORPUS_MODES",
    "extend_pair_target_anchor_corpus",
    "is_pair_target_anchor_corpus_mode",
]
