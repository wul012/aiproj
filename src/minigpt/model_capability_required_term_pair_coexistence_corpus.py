from __future__ import annotations


PAIR_COEXISTENCE_CORPUS_MODES = (
    "spaced_answer",
    "colon_immediate",
    "colon_immediate_first_token_boost",
    "colon_immediate_isolated_prompt",
    "colon_immediate_loss_calibrated",
    "equals_surface_fixed_repair",
    "equals_surface_balanced_repair",
    "equals_surface_tied_repair",
    "equals_surface_no_pair_id_repair",
    "equals_surface_no_pair_id_loss_balanced_repair",
)


def build_pair_coexistence_refresh_corpus(*, repeat: int, bridge_repeat: int, corpus_mode: str = "spaced_answer") -> str:
    lines = [
        "MiniGPT fixed/loss pair coexistence refresh corpus.",
        "The prompt before the colon selects the exact continuation term.",
    ]
    if corpus_mode == "spaced_answer":
        _extend_spaced_answer(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "colon_immediate":
        _extend_colon_immediate(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "colon_immediate_first_token_boost":
        _extend_first_token_boost(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "colon_immediate_isolated_prompt":
        _extend_isolated_prompt(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "colon_immediate_loss_calibrated":
        _extend_loss_calibrated(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "equals_surface_fixed_repair":
        _extend_equals_surface_fixed_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "equals_surface_balanced_repair":
        _extend_equals_surface_balanced_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "equals_surface_tied_repair":
        _extend_equals_surface_tied_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "equals_surface_no_pair_id_repair":
        _extend_equals_surface_no_pair_id_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    elif corpus_mode == "equals_surface_no_pair_id_loss_balanced_repair":
        _extend_equals_surface_no_pair_id_loss_balanced_repair(lines, repeat=repeat, bridge_repeat=bridge_repeat)
    else:
        raise ValueError(f"unknown corpus_mode: {corpus_mode}")
    return "\n".join(lines) + "\n"


def source_prompts(corpus_mode: str) -> tuple[str, str]:
    if corpus_mode in (
        "equals_surface_fixed_repair",
        "equals_surface_balanced_repair",
        "equals_surface_tied_repair",
        "equals_surface_no_pair_id_repair",
        "equals_surface_no_pair_id_loss_balanced_repair",
    ):
        return "fixed=", "loss="
    return "fixed:", "loss:"


def _extend_spaced_answer(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed: fixed",
                "loss: loss",
                "comparison-baseline|fixed: fixed",
                "factual-val-loss|loss: loss",
                "term=fixed prompt=fixed: answer=fixed",
                "term=loss prompt=loss: answer=loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "fixed and loss are separate branches.",
                "fixed: fixed ; loss: loss",
                "When the prefix is fixed:, continue fixed.",
                "When the prefix is loss:, continue loss.",
            ]
        )


def _extend_colon_immediate(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed:fixed",
                "loss:loss",
                "comparison-baseline|fixed:fixed",
                "factual-val-loss|loss:loss",
                "prompt=fixed:target=fixed",
                "prompt=loss:target=loss",
                "select fixed:fixed",
                "select loss:loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "fixed/loss are separate branches.",
                "fixed:fixed;loss:loss",
                "prefix fixed:fixed",
                "prefix loss:loss",
            ]
        )


def _extend_first_token_boost(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed:fixed",
                "loss:loss",
                "fixed:f",
                "loss:l",
                "fixed:fi",
                "loss:lo",
                "fixed:fix",
                "loss:los",
                "prompt=fixed:target=fixed",
                "prompt=loss:target=loss",
                "prefix=fixed:next=fixed",
                "prefix=loss:next=loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "fixed:fixed",
                "loss:loss",
                "fixed branch starts with f.",
                "loss branch starts with l.",
            ]
        )


def _extend_isolated_prompt(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "[fixed-objective]",
                "prompt fixed:",
                "target fixed",
                "fixed:fixed",
                "fixed:f",
                "fixed:fi",
                "fixed:fix",
                "fixed branch answer fixed",
                "[/fixed-objective]",
                "[loss-objective]",
                "prompt loss:",
                "target loss",
                "loss:loss",
                "loss:l",
                "loss:lo",
                "loss:los",
                "loss branch answer loss",
                "[/loss-objective]",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "fixed prompt stays in the fixed objective.",
                "loss prompt stays in the loss objective.",
                "fixed:fixed",
                "loss:loss",
            ]
        )


def _extend_loss_calibrated(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed:fixed",
                "loss:loss",
                "loss:loss",
                "comparison-baseline|fixed:fixed",
                "factual-val-loss|loss:loss",
                "prompt=fixed:target=fixed",
                "prompt=loss:target=loss",
                "loss prompt selects loss",
                "fixed prompt selects fixed",
                "when prefix is loss: continue loss",
                "when prefix is fixed: continue fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "calibrate fixed:fixed against loss:loss",
                "loss:loss;fixed:fixed",
                "loss prompt should not continue fixed",
                "fixed prompt should not continue loss",
            ]
        )


def _extend_equals_surface_fixed_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "fixed=f",
                "fixed=fi",
                "fixed=fix",
                "loss=l",
                "loss=lo",
                "loss=los",
                "prompt=fixed=target=fixed",
                "prompt=loss=target=loss",
                "equals surface fixed=fixed",
                "equals surface loss=loss",
                "fixed= selects fixed",
                "loss= selects loss",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "repair equals prompt surface for fixed.",
                "fixed= should continue fixed.",
                "loss= should continue loss.",
                "fixed= is not loss.",
                "loss= is not fixed.",
            ]
        )


def _extend_equals_surface_balanced_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "fixed=fixed",
                "loss=loss",
                "fixed=f",
                "loss=l",
                "fixed=fi",
                "loss=lo",
                "fixed=fix",
                "loss=los",
                "fixed=fixed",
                "loss=loss",
                "prompt=fixed=target=fixed",
                "prompt=loss=target=loss",
                "equals surface fixed=fixed",
                "equals surface loss=loss",
                "fixed= selects fixed",
                "loss= selects loss",
                "fixed= should not continue loss",
                "loss= should not continue fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "balanced equals prompt surface.",
                "fixed= should continue fixed.",
                "loss= should continue loss.",
                "fixed= and loss= are separate equals branches.",
                "fixed=fixed;loss=loss",
            ]
        )


def _extend_equals_surface_tied_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "pair=01 fixed=fixed loss=loss",
                "pair=01 loss=loss fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "prompt=fixed=target=fixed pair=01",
                "prompt=loss=target=loss pair=01",
                "fixed=next=fixed partner=loss",
                "loss=next=loss partner=fixed",
                "fixed= continues fixed while loss= continues loss",
                "loss= continues loss while fixed= continues fixed",
                "select pair=01 fixed=fixed loss=loss",
                "select pair=01 loss=loss fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "tied equals repair keeps fixed and loss in one pair.",
                "pair=01 means fixed=fixed and loss=loss together.",
                "fixed= should continue fixed; loss= should continue loss.",
                "do not trade fixed for loss; keep both branches.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_equals_surface_no_pair_id_repair(lines: list[str], *, repeat: int, bridge_repeat: int) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "record fixed=fixed loss=loss",
                "record loss=loss fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "fixed=fixed loss=loss",
                "loss=loss fixed=fixed",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "fixed=next fixed",
                "loss=next loss",
                "fixed= continues fixed while loss= continues loss",
                "loss= continues loss while fixed= continues fixed",
                "select fixed=fixed loss=loss",
                "select loss=loss fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "no pair id appears after equals.",
                "fixed= should continue fixed; loss= should continue loss.",
                "the paired record keeps both branches without numeric id tokens.",
                "do not trade fixed for loss; keep both branches.",
                "fixed=fixed|loss=loss",
            ]
        )


def _extend_equals_surface_no_pair_id_loss_balanced_repair(
    lines: list[str],
    *,
    repeat: int,
    bridge_repeat: int,
) -> None:
    for _ in range(max(1, repeat)):
        lines.extend(
            [
                "record fixed=fixed loss=loss",
                "record loss=loss fixed=fixed",
                "fixed=fixed",
                "loss=loss",
                "loss=loss",
                "fixed=fixed loss=loss",
                "loss=loss fixed=fixed",
                "prompt fixed= target fixed",
                "prompt loss= target loss",
                "prompt loss= target loss",
                "fixed=next fixed",
                "loss=next loss",
                "loss=next loss",
                "fixed= continues fixed while loss= continues loss",
                "loss= continues loss while fixed= continues fixed",
                "loss= should not continue fixed",
                "select fixed=fixed loss=loss",
                "select loss=loss fixed=fixed",
                "select loss=loss fixed=fixed",
            ]
        )
    for _ in range(max(0, bridge_repeat)):
        lines.extend(
            [
                "no pair id appears after equals.",
                "loss branch gets extra no-id balance.",
                "fixed= should continue fixed; loss= should continue loss.",
                "loss= should not drift into fixed.",
                "the paired record keeps both branches without numeric id tokens.",
                "fixed=fixed|loss=loss",
            ]
        )


__all__ = [
    "PAIR_COEXISTENCE_CORPUS_MODES",
    "build_pair_coexistence_refresh_corpus",
    "source_prompts",
]
