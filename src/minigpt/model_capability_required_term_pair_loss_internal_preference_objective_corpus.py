from __future__ import annotations


PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES = (
    "equals_surface_no_pair_id_loss_internal_preference_repair",
    "equals_surface_no_pair_id_loss_internal_first_token_repair",
    "equals_surface_no_pair_id_loss_internal_ranked_choice_repair",
    "equals_surface_no_pair_id_loss_internal_fixed_bridge_repair",
    "equals_surface_no_pair_id_loss_internal_joint_cycle_repair",
    "equals_surface_no_pair_id_loss_internal_balanced_anchor_repair",
    "equals_surface_no_pair_id_loss_internal_joint_cycle_internal_repair",
    "equals_surface_no_pair_id_loss_internal_joint_cycle_light_merge_repair",
    "equals_surface_no_pair_id_loss_internal_surface_first_schedule_repair",
    "equals_surface_no_pair_id_loss_internal_loss_guarded_schedule_repair",
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
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_fixed_bridge_repair":
        _extend_fixed_bridge_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_joint_cycle_repair":
        _extend_joint_cycle_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_balanced_anchor_repair":
        _extend_balanced_anchor_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_joint_cycle_internal_repair":
        _extend_joint_cycle_internal_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_joint_cycle_light_merge_repair":
        _extend_joint_cycle_light_merge_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_surface_first_schedule_repair":
        _extend_surface_first_schedule_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
        return True
    if corpus_mode == "equals_surface_no_pair_id_loss_internal_loss_guarded_schedule_repair":
        _extend_loss_guarded_schedule_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
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


def _extend_fixed_bridge_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "fixed=fixed",
                "fixed=fixed",
                "loss=l",
                "loss=lo",
                "loss=los",
                "loss=loss",
                "loss=loss",
                "bridge fixed= fixed while loss= remains loss",
                "decode bridge fixed= should generate fixed",
                "decode bridge loss= should generate loss",
                "internal fixed= prefers fixed",
                "internal loss= prefers loss",
                "fixed generation bridge closes the fixed gap",
                "loss internal preference remains visible",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "bridge objective restores fixed generation without erasing loss preference.",
                "fixed= fixed is the missing generation bridge.",
                "loss= loss remains the internal preference anchor.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_joint_cycle_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "joint cycle fixed=fixed loss=loss",
                "joint cycle loss=loss fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed",
                "loss=loss",
                "fixed=f fixed=fi fixed=fix fixed=fixed",
                "loss=l loss=lo loss=los loss=loss",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
                "generation fixed= fixed",
                "generation loss= loss",
                "internal fixed= candidate fixed rank 1",
                "internal loss= candidate loss rank 1",
                "decode fixed= fixed while decode loss= loss",
                "do not trade fixed for loss",
                "do not trade loss for fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "joint cycle keeps generation and internal preference in the same clean record.",
                "fixed= fixed and loss= loss are both required.",
                "loss remains loss while fixed remains fixed.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_balanced_anchor_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "anchor fixed prompt fixed= target fixed",
                "anchor loss prompt loss= target loss",
                "anchor fixed prompt fixed= target fixed",
                "anchor loss prompt loss= target loss",
                "fixed=fixed",
                "loss=loss",
                "fixed=next fixed",
                "loss=next loss",
                "fixed branch generation fixed",
                "loss branch generation loss",
                "fixed branch internal fixed",
                "loss branch internal loss",
                "forced choice fixed= fixed",
                "forced choice loss= loss",
                "balanced anchor fixed=fixed loss=loss",
                "balanced anchor loss=loss fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "balanced anchors repeat both prompts with equal weight.",
                "fixed generation and loss generation must coexist.",
                "internal preference mirrors generation preference.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_joint_cycle_internal_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "joint cycle fixed=fixed loss=loss",
                "joint cycle loss=loss fixed=fixed",
                "generation fixed= fixed",
                "generation loss= loss",
                "fixed=f fixed=fi fixed=fix fixed=fixed",
                "loss=l loss=lo loss=los loss=loss",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
                "teacher forced fixed= fixed",
                "teacher forced loss= loss",
                "forced choice fixed= fixed",
                "forced choice loss= loss",
                "internal fixed= candidate fixed rank 1",
                "internal fixed= candidate loss rank 2",
                "internal loss= candidate loss rank 1",
                "internal loss= candidate fixed rank 2",
                "score fixed= fixed lower than loss",
                "score loss= loss lower than fixed",
                "preserve generation fixed= fixed",
                "preserve generation loss= loss",
                "repair internal loss= prefers loss",
                "do not trade fixed for loss",
                "do not trade loss for fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "joint-cycle internal repair keeps the v630 generation pair-full route.",
                "loss= must internally prefer loss while fixed= keeps fixed.",
                "teacher-forced loss rows repair the v631 internal gap.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_joint_cycle_light_merge_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "joint cycle fixed=fixed loss=loss",
                "joint cycle loss=loss fixed=fixed",
                "generation fixed= fixed",
                "generation loss= loss",
                "fixed=f fixed=fi fixed=fix fixed=fixed",
                "loss=l loss=lo loss=los loss=loss",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
                "decode fixed= fixed while decode loss= loss",
                "internal fixed= candidate fixed rank 1",
                "internal loss= candidate loss rank 1",
                "light merge keeps generation first",
                "light merge repairs internal loss softly",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "light merge preserves v630 generation pair-full before adding internal repair.",
                "loss= should prefer loss without erasing fixed= fixed.",
                "fixed= fixed and loss= loss remain the surface targets.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_surface_first_schedule_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "surface stage fixed=fixed loss=loss",
                "surface stage loss=loss fixed=fixed",
                "generation fixed= fixed",
                "generation fixed= fixed",
                "generation loss= loss",
                "generation loss= loss",
                "fixed=f fixed=fi fixed=fix fixed=fixed",
                "loss=l loss=lo loss=los loss=loss",
                "prompt fixed= answer fixed",
                "prompt loss= answer loss",
                "fixed surface target remains fixed",
                "loss surface target remains loss",
                "schedule boundary no checkpoint resume",
                "internal stage fixed candidate fixed rank 1",
                "internal stage fixed candidate loss rank 2",
                "internal stage loss candidate loss rank 1",
                "internal stage loss candidate fixed rank 2",
                "surface first keeps fixed before internal repair",
                "surface first keeps loss before internal repair",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "surface-first schedule approximates two-stage training in one corpus.",
                "generation pair-full remains the gate before internal repair.",
                "loss internal repair is a soft second-stage hint.",
                "not checkpoint resume; this is a corpus schedule approximation.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_loss_guarded_schedule_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "loss guard surface loss=loss fixed=fixed",
                "loss guard surface fixed=fixed loss=loss",
                "generation loss= loss",
                "generation loss= loss",
                "generation loss= loss",
                "generation fixed= fixed",
                "generation fixed= fixed",
                "loss=l loss=lo loss=los loss=loss",
                "fixed=f fixed=fi fixed=fix fixed=fixed",
                "prompt loss= answer loss",
                "prompt loss= answer loss",
                "prompt fixed= answer fixed",
                "loss guard first token after loss= is l",
                "loss guard continuation after loss= is loss",
                "internal stage loss candidate loss rank 1",
                "internal stage loss candidate fixed rank 2",
                "internal stage fixed candidate fixed rank 1",
                "internal stage fixed candidate loss rank 2",
                "do not collapse loss into fixed",
                "fixed stays fixed while loss stays loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "loss-guarded schedule counters the fixed-only collapse from surface-first.",
                "loss= must stay loss before fixed repair is accepted.",
                "generation pair-full remains required after adding the loss guard.",
                "not checkpoint resume; this is a loss-guarded corpus approximation.",
                "fixed=fixed|loss=loss",
            ]
        )


__all__ = [
    "PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES",
    "extend_pair_loss_internal_preference_objective_corpus",
    "is_pair_loss_internal_preference_objective_corpus_mode",
]
