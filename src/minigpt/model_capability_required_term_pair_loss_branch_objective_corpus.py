from __future__ import annotations


PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES = (
    "equals_surface_no_pair_id_loss_branch_targeted_repair",
    "equals_surface_no_pair_id_loss_branch_dual_anchor_repair",
    "equals_surface_no_pair_id_loss_branch_micro_span_repair",
)


def extend_pair_loss_branch_objective_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_loss_branch_targeted_repair":
        _extend_targeted_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_branch_dual_anchor_repair":
        _extend_dual_anchor_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_branch_micro_span_repair":
        _extend_micro_span_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    return False


def is_pair_loss_branch_objective_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES


def _extend_targeted_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "record fixed=fixed loss=loss",
                "record loss=loss fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "loss=loss",
                "loss=loss",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "prompt loss= target loss",
                "fixed=next fixed",
                "loss=next loss",
                "loss=next loss",
                "loss branch target loss",
                "loss branch target loss",
                "fixed branch target fixed",
                "loss= should continue loss immediately",
                "fixed= should continue fixed immediately",
                "loss= should not drift into fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "loss-branch objective keeps the missed branch visible.",
                "loss=loss is the direct target after loss=.",
                "fixed=fixed remains the direct target after fixed=.",
                "loss= should not trade into fixed.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_dual_anchor_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "loss=loss|fixed=fixed",
                "fixed=fixed|loss=loss",
                "anchor loss=loss",
                "anchor fixed=fixed",
                "target loss=loss",
                "target fixed=fixed",
                "loss=loss",
                "loss=loss",
                "fixed=fixed",
                "loss=next loss",
                "fixed=next fixed",
                "loss branch answer loss",
                "fixed branch answer fixed",
                "loss first then fixed: loss=loss fixed=fixed",
                "fixed first then loss: fixed=fixed loss=loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "dual anchors keep loss and fixed in the same clean record.",
                "loss=loss|fixed=fixed",
                "fixed=fixed|loss=loss",
                "the loss branch is not a negative example for fixed.",
                "the fixed branch is not a negative example for loss.",
            ]
        )


def _extend_micro_span_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
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
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "micro span fixed= f fi fix fixed",
                "micro span loss= l lo los loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "micro span hints expose the first loss token without pair ids.",
                "after loss= the next token is l.",
                "after fixed= the next token is f.",
                "loss=loss and fixed=fixed remain clean direct targets.",
                "fixed=fixed|loss=loss",
            ]
        )


__all__ = [
    "PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_MODES",
    "extend_pair_loss_branch_objective_corpus",
    "is_pair_loss_branch_objective_corpus_mode",
]
