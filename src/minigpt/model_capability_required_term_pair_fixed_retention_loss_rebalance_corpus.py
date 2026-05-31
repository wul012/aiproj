from __future__ import annotations


PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES = (
    "equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair",
    "equals_surface_no_pair_id_fixed_retention_dual_cycle_repair",
)


def extend_pair_fixed_retention_loss_rebalance_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair":
        _extend_loss_rebalance_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_fixed_retention_dual_cycle_repair":
        _extend_dual_cycle_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_fixed_retention_loss_rebalance_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES


def _extend_loss_rebalance_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
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
                "loss=loss",
                "fixed=fixed",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "first token fixed= f",
                "first token loss= l",
                "fixed branch answer fixed",
                "loss branch answer loss",
                "fixed=fixed|loss=loss",
                "loss=loss|fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "loss rebalance restores loss while retaining fixed first-token rows.",
                "fixed= must continue fixed and loss= must continue loss.",
                "fixed=fixed remains visible after fixed=.",
                "loss=loss remains visible after loss=.",
            ]
        )


def _extend_dual_cycle_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    cycle = [
        "fixed=fixed",
        "loss=loss",
        "fixed=f",
        "loss=l",
        "fixed=fi",
        "loss=lo",
        "fixed=fix",
        "loss=los",
        "fixed=fixed loss=loss",
        "loss=loss fixed=fixed",
        "prompt fixed= target fixed",
        "prompt loss= target loss",
    ]
    for _ in range(max(1, repeat)):
        lines.extend(cycle)
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "dual cycle alternates fixed and loss targets without pair ids.",
                "fixed first-token retention and loss recovery share the same cycle.",
                "fixed= should not erase loss= and loss= should not erase fixed=.",
                "fixed=fixed|loss=loss",
            ]
        )


__all__ = [
    "PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES",
    "extend_pair_fixed_retention_loss_rebalance_corpus",
    "is_pair_fixed_retention_loss_rebalance_corpus_mode",
]
