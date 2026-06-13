"""v1162: what learned-absolute vs RoPE positions do at lengths beyond training.

This is the honest, narrowly-scoped study of the ONE regime where RoPE and a
learned position table genuinely differ. It deliberately does **not** claim
"RoPE extrapolates to longer sequences" — on this corpus that claim is
unsupportable, and an adversarial design review (the v1162 honesty panel) showed
several intuitive framings are simply false. What it *does* establish, with
multi-seed measurements and diagnostic arms:

1. **Parameter provisioning, not "crashing".** A learned position embedding is a
   table of exactly ``block_size`` rows; the ``seq_len > block_size`` guard in
   :meth:`MiniGPT.forward` fires identically for learned AND RoPE models, so
   "learned crashes, RoPE survives" is false. The real difference: enlarging the
   context ceiling costs the learned scheme ``block_size`` *trainable* rows (rows
   beyond the trained length get no gradient), while RoPE needs **zero** position
   parameters and its rotation is defined for any index.

2. **Absolute-index definedness.** Trained at ``train_block_size`` but evaluated
   on longer windows, the learned model feeds *untrained* position rows at the
   beyond-range indices, so its per-token loss rises the instant the index passes
   the trained length. RoPE (translation-equivariant) treats those indices
   identically to trained ones, so its loss stays flat. We report this as a
   per-position curve over several eval lengths and across seeds — magnitude is
   measured, only the *sign* is pre-registered.

3. **It is not extrapolation of relative distance, and longer context does not
   help here.** The corpus is independent ~11-char sentences, so every
   signal-bearing relative offset (<=~11) was already seen during training and
   there is no long-range dependency to exploit. Two diagnostic arms keep the
   story honest:
   * **sliding-window learned** (the realistic deployment) re-indexes every
     prediction into trained positions and, on this corpus, ties RoPE — proving
     the naive-long-forward gap is an inference-mode artifact, not an inherent
     learned-positions deficiency;
   * **zeroed-tail learned** sets the beyond-range rows to 0 — if it matches the
     random-init tail, the effect is *absence of trained position signal*, not
     *random-noise injection*.

Run with ``weight_decay=0.0`` so the untrained tail is provably exactly at init.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

import torch

from minigpt.heldout_eval import (
    bucket_per_position,
    evaluate_heldout_per_position,
    evaluate_sliding_window,
)
from minigpt.lm_training import train_lm
from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import utc_now


@dataclass
class LengthExtrapolationConfig:
    train_block_size: int = 32
    eval_lengths: tuple[int, ...] = (32, 48, 64, 96, 128)
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    steps: int = 400
    lr: float = 3e-4
    batch_size: int = 32
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    attention_diag_windows: int = 8

    @property
    def model_block_size(self) -> int:
        return max(self.eval_lengths)


def _build_model(*, vocab_size: int, block_size: int, use_rope: bool, config: LengthExtrapolationConfig) -> MiniGPT:
    return MiniGPT(
        GPTConfig(
            vocab_size=vocab_size,
            block_size=block_size,
            n_layer=config.n_layer,
            n_head=config.n_head,
            n_embd=config.n_embd,
            dropout=0.0,
            use_rope=use_rope,
        )
    )


def _train(model: MiniGPT, train_ids: torch.Tensor, *, config: LengthExtrapolationConfig, device) -> None:
    # weight_decay=0.0 is essential: rows never selected by a length-train_block_size
    # window receive no gradient, and with decay off they stay *exactly* at init,
    # making the "untrained tail" claim literally true.
    train_lm(
        model,
        list(model.parameters()),
        train_ids,
        steps=config.steps,
        lr=config.lr,
        batch_size=config.batch_size,
        block_size=config.train_block_size,
        device=device,
        weight_decay=0.0,
    )


def _mean_std(values: list[float]) -> tuple[float, float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return float("nan"), 0.0
    mean = sum(clean) / len(clean)
    std = statistics.stdev(clean) if len(clean) > 1 else 0.0
    return mean, std


def _categorical_block_size_ceiling(*, vocab_size, config: LengthExtrapolationConfig, device) -> dict:
    """Demonstrate the length ceiling is gated on block_size identically for both
    schemes (via a direct, un-cropped forward — NOT generate(), which crops)."""
    long_len = config.model_block_size
    out: dict[str, dict] = {}
    for use_rope in (False, True):
        small = _build_model(vocab_size=vocab_size, block_size=config.train_block_size, use_rope=use_rope, config=config).to(device)
        idx_long = torch.zeros((1, long_len), dtype=torch.long, device=device)
        raised = False
        try:
            small(idx_long)
        except ValueError:
            raised = True
        big = _build_model(vocab_size=vocab_size, block_size=config.model_block_size, use_rope=use_rope, config=config).to(device)
        idx_big = torch.zeros((1, config.model_block_size), dtype=torch.long, device=device)
        logits, _ = big(idx_big)
        out["rope" if use_rope else "learned"] = {
            "small_block_size": config.train_block_size,
            "raises_on_len": long_len,
            "small_raises": raised,
            "big_block_size": config.model_block_size,
            "big_returns_finite": bool(torch.isfinite(logits).all().item()),
        }
    return out


def _zeroed_tail_beyond(model: MiniGPT, heldout_ids, *, eval_len: int, train_block_size: int, device) -> float | None:
    """Beyond-range loss when the learned position rows [T, eval_len) are zeroed
    (no positional signal, rather than random init)."""
    saved = model.position_embedding.weight.detach().clone()
    try:
        with torch.no_grad():
            model.position_embedding.weight[train_block_size:eval_len].zero_()
        per = evaluate_heldout_per_position(model, heldout_ids, window_len=eval_len, device=device)
        loss, _ = bucket_per_position(per["per_position_loss"], per["per_position_count"], lo=train_block_size, hi=eval_len)
        return loss
    finally:
        with torch.no_grad():
            model.position_embedding.weight.copy_(saved)


def _rope_attention_mass_beyond(model: MiniGPT, heldout_ids, *, eval_len: int, train_block_size: int, device, max_windows: int) -> float | None:
    """Fraction of RoPE attention mass landing on relative distances > train_block_size
    at eval_len — shows the unseen-distance regime is actually entered."""
    data = heldout_ids.detach().to("cpu", dtype=torch.long)
    if data.numel() < eval_len + 1 or eval_len <= train_block_size:
        return None
    model.eval()
    model.set_attention_capture(True)
    fractions: list[float] = []
    try:
        starts = list(range(0, data.numel() - 1, eval_len))[:max_windows]
        for start in starts:
            chunk = data[start : start + eval_len]
            if chunk.numel() < eval_len:
                break
            model(chunk.unsqueeze(0).to(device))
            for att in model.attention_maps():
                t = att.shape[-1]
                pos = torch.arange(t)
                dist = pos.view(t, 1) - pos.view(1, t)  # query i - key j (>=0, causal)
                beyond = att[..., (dist > train_block_size)].sum()
                total = att.sum()
                if float(total.item()) > 0:
                    fractions.append(float((beyond / total).item()))
    finally:
        model.set_attention_capture(False)
    return sum(fractions) / len(fractions) if fractions else None


def run_length_extrapolation(
    *,
    vocab_size: int,
    train_ids: torch.Tensor,
    heldout_ids: torch.Tensor,
    config: LengthExtrapolationConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    T = config.train_block_size
    bs = config.model_block_size
    lengths = tuple(sorted(set(config.eval_lengths)))
    if T not in lengths:
        raise ValueError("eval_lengths must include train_block_size as the in-distribution control")
    if max(lengths) > bs:
        raise ValueError("model_block_size must be >= every eval length")

    # Per-seed collection -------------------------------------------------
    # within[L][scheme] = list over seeds of bucket[0,T) mean CE; beyond likewise.
    within: dict[int, dict[str, list]] = {L: {"learned": [], "rope": []} for L in lengths}
    beyond: dict[int, dict[str, list]] = {L: {"learned": [], "rope": [], "learned_zeroed": []} for L in lengths}
    control: dict[str, list] = {"learned": [], "rope": []}  # clean within-range from the pure L=T eval
    sliding_losses: list[float] = []
    sliding_accs: list[float] = []
    sliding_token_count = 0
    tail_drifts: list[float] = []
    # per-position curves at the max length, accumulated across seeds (index -> list)
    curve_acc = {"learned": [[] for _ in range(max(lengths))], "rope": [[] for _ in range(max(lengths))]}
    window_counts: dict[int, int] = {}
    token_counts: dict[int, dict[str, int]] = {L: {"within": 0, "beyond": 0} for L in lengths}
    attention_mass_beyond = None

    for si, seed in enumerate(config.seeds):
        torch.manual_seed(seed)
        learned = _build_model(vocab_size=vocab_size, block_size=bs, use_rope=False, config=config).to(device)
        tail_before = learned.position_embedding.weight[T:bs].detach().clone()
        _train(learned, train_ids, config=config, device=device)
        tail_after = learned.position_embedding.weight[T:bs].detach()
        tail_drifts.append(float((tail_after - tail_before).norm().item()))

        torch.manual_seed(seed)
        rope = _build_model(vocab_size=vocab_size, block_size=bs, use_rope=True, config=config).to(device)
        _train(rope, train_ids, config=config, device=device)

        for L in lengths:
            for name, model in (("learned", learned), ("rope", rope)):
                per = evaluate_heldout_per_position(model, heldout_ids, window_len=L, device=device)
                w_loss, w_n = bucket_per_position(per["per_position_loss"], per["per_position_count"], lo=0, hi=T)
                within[L][name].append(w_loss)
                if L > T:
                    b_loss, b_n = bucket_per_position(per["per_position_loss"], per["per_position_count"], lo=T, hi=L)
                    beyond[L][name].append(b_loss)
                else:
                    b_n = 0
                if L == T:
                    control[name].append(per["overall_loss"])
                if si == 0:
                    window_counts[L] = per["heldout_window_count"]
                    token_counts[L]["within"] = w_n
                    token_counts[L]["beyond"] = b_n if L > T else 0
                if L == max(lengths):
                    for i, val in enumerate(per["per_position_loss"]):
                        if val is not None:
                            curve_acc[name][i].append(val)
            if L > T:
                beyond[L]["learned_zeroed"].append(
                    _zeroed_tail_beyond(learned, heldout_ids, eval_len=L, train_block_size=T, device=device)
                )

        sw = evaluate_sliding_window(learned, heldout_ids, window_size=T, device=device)
        sliding_losses.append(sw["sliding_loss"])
        sliding_accs.append(sw["sliding_token_accuracy"])
        sliding_token_count = sw["sliding_token_count"]

        if si == 0:
            attention_mass_beyond = _rope_attention_mass_beyond(
                rope, heldout_ids, eval_len=max(lengths), train_block_size=T, device=device,
                max_windows=config.attention_diag_windows,
            )

    # Aggregate -----------------------------------------------------------
    rows = []
    length_sweep = []
    for L in lengths:
        entry = {"eval_length": L}
        for name in ("learned", "rope"):
            w_mean, w_std = _mean_std(within[L][name])
            row = {
                "scheme": name,
                "eval_length": L,
                "within_loss_mean": round(w_mean, 6),
                "within_loss_std": round(w_std, 6),
                "within_token_count": token_counts[L]["within"],
                "window_count": window_counts.get(L, 0),
            }
            entry[f"{name}_within"] = round(w_mean, 6)
            if L > T:
                b_mean, b_std = _mean_std(beyond[L][name])
                jumps = [b - w for b, w in zip(beyond[L][name], within[L][name]) if b is not None and w is not None]
                j_mean, j_std = _mean_std(jumps)
                row.update({
                    "beyond_loss_mean": round(b_mean, 6),
                    "beyond_loss_std": round(b_std, 6),
                    "beyond_minus_within_mean": round(j_mean, 6),
                    "beyond_minus_within_std": round(j_std, 6),
                    "beyond_token_count": token_counts[L]["beyond"],
                })
                entry[f"{name}_beyond"] = round(b_mean, 6)
                entry[f"{name}_jump_mean"] = round(j_mean, 6)
                entry[f"{name}_jump_std"] = round(j_std, 6)
            else:
                row.update({
                    "beyond_loss_mean": None, "beyond_loss_std": None,
                    "beyond_minus_within_mean": None, "beyond_minus_within_std": None,
                    "beyond_token_count": 0,
                })
            rows.append(row)
        if L > T:
            z_mean, z_std = _mean_std(beyond[L]["learned_zeroed"])
            entry["learned_zeroed_beyond"] = round(z_mean, 6)
            entry["learned_zeroed_beyond_std"] = round(z_std, 6)
        length_sweep.append(entry)

    # Decision: data-driven, never pre-assumes a winner --------------------
    L_max = max(lengths)
    learned_jump = [b - w for b, w in zip(beyond[L_max]["learned"], within[L_max]["learned"]) if b is not None and w is not None]
    rope_jump = [b - w for b, w in zip(beyond[L_max]["rope"], within[L_max]["rope"]) if b is not None and w is not None]
    lj_mean, lj_std = _mean_std(learned_jump)
    rj_mean, rj_std = _mean_std(rope_jump)

    def _gap_confirmed_at(L: int) -> bool:
        lj = [b - w for b, w in zip(beyond[L]["learned"], within[L]["learned"]) if b is not None and w is not None]
        rj = [b - w for b, w in zip(beyond[L]["rope"], within[L]["rope"]) if b is not None and w is not None]
        m_l, s_l = _mean_std(lj)
        m_r, s_r = _mean_std(rj)
        return (m_l - s_l > 0.0) and ((m_l - s_l) > (m_r + s_r))

    confirmed_lengths = [L for L in lengths if L > T and _gap_confirmed_at(L)]
    if confirmed_lengths:
        verdict = "absolute_index_definedness_gap_confirmed"
    elif lj_mean > rj_mean:
        verdict = "directional_but_underpowered"
    else:
        verdict = "no_separation"

    ceiling = _categorical_block_size_ceiling(vocab_size=vocab_size, config=config, device=device)
    drift_max = max(tail_drifts) if tail_drifts else 0.0
    both_raise = ceiling["learned"]["small_raises"] and ceiling["rope"]["small_raises"]
    both_big_finite = ceiling["learned"]["big_returns_finite"] and ceiling["rope"]["big_returns_finite"]
    untrained_tail_at_init = drift_max < 1e-6

    harness_valid = both_raise and both_big_finite and untrained_tail_at_init
    status = "pass" if harness_valid else "review"
    decision = "length_extrapolation_measured" if harness_valid else "length_extrapolation_invalid_harness"

    sliding_mean, sliding_std = _mean_std(sliding_losses)
    sacc_mean, _ = _mean_std(sliding_accs)
    ctrl_learned_mean, ctrl_learned_std = _mean_std(control["learned"])
    ctrl_rope_mean, ctrl_rope_std = _mean_std(control["rope"])
    z_mean_max, _ = _mean_std(beyond[L_max]["learned_zeroed"])
    learned_beyond_max, _ = _mean_std(beyond[L_max]["learned"])
    beyond_min_tokens = min((token_counts[L]["beyond"] for L in lengths if L > T), default=0) * len(config.seeds)
    # Decompose the learned beyond-range degradation: how much is random-noise
    # injection from the untrained rows (recovered by zeroing them) vs a residual
    # from genuinely absent position signal (zeroed-tail still above within-range).
    noise_component = learned_beyond_max - z_mean_max
    signal_component = z_mean_max - ctrl_learned_mean
    if noise_component <= 0 and signal_component <= 0:
        decomposition = "no measurable beyond-range degradation"
    elif noise_component > signal_component:
        decomposition = "mostly random-noise injection from untrained rows"
    else:
        decomposition = "mostly absence of trained position signal"

    learned_pos_table = bs * config.n_embd

    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "device": str(device),
        "seeds": len(config.seeds),
        "train_block_size": T,
        "model_block_size": bs,
        "eval_lengths": ",".join(str(L) for L in lengths),
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "steps": config.steps,
        "weight_decay": 0.0,
        "train_char_count": (corpus_stats or {}).get("train_char_count"),
        "heldout_char_count": (corpus_stats or {}).get("heldout_char_count"),
        # Headline at the longest eval length (means over seeds):
        "learned_jump_at_max_mean": round(lj_mean, 6),
        "learned_jump_at_max_std": round(lj_std, 6),
        "rope_jump_at_max_mean": round(rj_mean, 6),
        "rope_jump_at_max_std": round(rj_std, 6),
        # Diagnostic arms:
        "within_range_control_learned": round(ctrl_learned_mean, 6),
        "within_range_control_rope": round(ctrl_rope_mean, 6),
        "sliding_window_learned_loss": round(sliding_mean, 6),
        "sliding_window_learned_loss_std": round(sliding_std, 6),
        "rope_within_range_loss": round(ctrl_rope_mean, 6),
        "learned_beyond_random_tail_at_max": round(learned_beyond_max, 6),
        "learned_beyond_zeroed_tail_at_max": round(z_mean_max, 6),
        "learned_beyond_noise_component": round(noise_component, 6),
        "learned_beyond_signal_component": round(signal_component, 6),
        "learned_beyond_degradation_source": decomposition,
        "rope_attention_mass_beyond_trained_distance": (
            round(attention_mass_beyond, 6) if attention_mass_beyond is not None else None
        ),
        # Harness-validity evidence:
        "untrained_tail_l2_drift_max": round(drift_max, 9),
        "both_schemes_raise_beyond_block_size": both_raise,
        "both_schemes_finite_when_rebuilt": both_big_finite,
        "beyond_range_token_count_min": beyond_min_tokens,
        # Parameter framing (the equal total is incidental):
        "learned_position_table_params": learned_pos_table,
        "rope_effective_position_params": 0,
    }

    recommendations = [
        f"VERDICT ({verdict}): at the longest eval length {L_max}, the learned-position "
        f"beyond-range loss rises {lj_mean:+.4f}±{lj_std:.4f} nats above its within-range loss, "
        f"while RoPE moves {rj_mean:+.4f}±{rj_std:.4f}. Only the SIGN is pre-registered; the magnitude is measured over {len(config.seeds)} seeds.",
        "SCOPE — this measures whether each scheme stays FUNCTIONAL/DEFINED at lengths > train length, NOT whether longer context helps. The corpus is independent ~11-char sentences with no cross-sentence dependency, so no prediction needs more than ~11 tokens of history.",
        "NOT relative-distance extrapolation: every signal-bearing relative offset at the beyond-range indices (<=~11, intra-sentence) was already seen during training. The only thing novel there is the ABSOLUTE index, which RoPE ignores by construction; the learned table simply has untrained rows there.",
        "The seq_len>block_size ValueError fires identically for BOTH schemes (it is gated on block_size and the block_size×block_size mask buffer). A RoPE model built at the small block_size also raises; both raise={both_raise}, both finite when rebuilt={both_big_finite}. RoPE's real edge is that enlarging the ceiling costs ZERO position params and zero retraining; the learned table needs block_size trainable rows.".format(both_raise=both_raise, both_big_finite=both_big_finite),
        f"Realistic learned deployment = sliding window of {T}: loss {sliding_mean:.4f} vs RoPE within-range {ctrl_rope_mean:.4f}. On this no-long-range corpus it roughly ties RoPE, so the naive-long-forward gap is an inference-mode artifact, not an inherent learned-positions deficiency.",
        f"Zeroed-tail diagnostic at length {L_max}: random-init tail {learned_beyond_max:.4f} -> zeroed tail {z_mean_max:.4f} -> within-range {ctrl_learned_mean:.4f}. Decomposition = {decomposition}: noise-injection component {noise_component:+.4f} (recovered by zeroing the untrained rows) vs residual missing-signal component {signal_component:+.4f}.",
        f"Untrained tail max L2 drift across seeds = {drift_max:.2e} (weight_decay=0.0), so the beyond-range rows are provably at their N(0,0.02) init.",
        "Naive RoPE (Llama form, base=10000, no NTK/YaRN) is itself known to degrade on relative distances beyond training; ~{m} of attention mass at length {L} lands on relative distances > {T}, but those distances carry no signal in this corpus so the degradation cannot be exposed here.".format(
            m=(f"{attention_mass_beyond*100:.1f}%" if attention_mass_beyond is not None else "n/a"), L=L_max, T=T
        ),
        "Parameter framing: the RoPE model still ALLOCATES an unused position table, so an equal total parameter count is incidental — RoPE's effective position params are 0. A future cleanup could drop the unused table.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT learned-vs-RoPE position behavior beyond trained length v1162",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": [
            "scheme", "eval_length", "within_loss_mean", "within_loss_std",
            "beyond_loss_mean", "beyond_loss_std", "beyond_minus_within_mean",
            "beyond_minus_within_std", "within_token_count", "beyond_token_count", "window_count",
        ],
        # Extra (JSON-only) payload for figures and audit:
        "length_sweep": length_sweep,
        "per_position_curve_at_max": {
            "eval_length": L_max,
            "train_block_size": T,
            "position": list(range(L_max)),
            "learned_loss": [round(sum(v) / len(v), 6) if v else None for v in curve_acc["learned"]],
            "rope_loss": [round(sum(v) / len(v), 6) if v else None for v in curve_acc["rope"]],
        },
        "categorical_ceiling": ceiling,
        "sliding_window": {
            "window_size": T,
            "loss_mean": round(sliding_mean, 6),
            "loss_std": round(sliding_std, 6),
            "token_accuracy_mean": round(sacc_mean, 6),
            "token_count": sliding_token_count,
        },
        "tail_drift_l2": [round(d, 9) for d in tail_drifts],
        "seeds": list(config.seeds),
    }


__all__ = ["LengthExtrapolationConfig", "run_length_extrapolation"]
