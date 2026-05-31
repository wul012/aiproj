from __future__ import annotations


PAIR_BRANCH_BINDING_CORPUS_MODES = (
    "equals_surface_no_pair_id_branch_binding_repair",
    "equals_surface_no_pair_id_branch_binding_no_space_repair",
)


def extend_pair_branch_binding_corpus(
    lines: list[str],
    *,
    corpus_mode: str,
    repeat: int,
    bridge_repeat: int,
) -> bool:
    if corpus_mode == "equals_surface_no_pair_id_branch_binding_repair":
        _extend_equals_surface_no_pair_id_branch_binding_repair(
            lines,
            repeat=repeat,
            bridge_repeat=bridge_repeat,
        )
        return True
    if corpus_mode == "equals_surface_no_pair_id_branch_binding_no_space_repair":
        _extend_equals_surface_no_pair_id_branch_binding_no_space_repair(
            lines,
            repeat=repeat,
            bridge_repeat=bridge_repeat,
        )
        return True
    return False


def is_pair_branch_binding_corpus_mode(corpus_mode: str) -> bool:
    return corpus_mode in PAIR_BRANCH_BINDING_CORPUS_MODES


def _extend_equals_surface_no_pair_id_branch_binding_repair(
    lines: list[str],
    *,
    repeat: int,
    bridge_repeat: int,
) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "branch fixed prompt fixed= answer fixed",
                "branch loss prompt loss= answer loss",
                "fixed=fixed",
                "loss=loss",
                "input fixed= output fixed",
                "input loss= output loss",
                "prompt fixed= expected fixed",
                "prompt loss= expected loss",
                "bind fixed= to fixed",
                "bind loss= to loss",
                "fixed= continues fixed only",
                "loss= continues loss only",
                "fixed= never continues loss",
                "loss= never continues fixed",
                "paired binding fixed=fixed loss=loss",
                "paired binding loss=loss fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "branch binding has no numeric pair id.",
                "the prompt token before equals selects its own continuation.",
                "fixed= is bound to fixed.",
                "loss= is bound to loss.",
                "fixed and loss are parallel labels, not replacements.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_equals_surface_no_pair_id_branch_binding_no_space_repair(
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
                "fixed=fixed loss=loss",
                "loss=loss fixed=fixed",
                "fixed=fixed|loss=loss",
                "loss=loss|fixed=fixed",
                "fixed=fixed;loss=loss",
                "loss=loss;fixed=fixed",
                "branch_fixed=fixed",
                "branch_loss=loss",
                "key_fixed=fixed",
                "key_loss=loss",
                "fixed=fixed_only",
                "loss=loss_only",
                "fixed=fixed_not_loss",
                "loss=loss_not_fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "no-space branch binding keeps fixed=fixed and loss=loss.",
                "after fixed= write fixed immediately.",
                "after loss= write loss immediately.",
                "fixed=fixed|loss=loss",
                "loss=loss|fixed=fixed",
            ]
        )


__all__ = [
    "PAIR_BRANCH_BINDING_CORPUS_MODES",
    "extend_pair_branch_binding_corpus",
    "is_pair_branch_binding_corpus_mode",
]
