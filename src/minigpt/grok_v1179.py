"""v1179: grokking — delayed generalization on modular arithmetic.

Trains a MiniGPT on ``a + b = c (mod p)`` with a fraction of the (a, b) pairs
held out, and measures the *grokking* signature: training accuracy saturates
early (memorization) while validation accuracy stays at chance for a long span,
then makes a sudden late phase transition to generalization. Weight decay is the
hypothesized driver; a paired ``weight_decay=0`` ablation tests that causally.

This pivots the version line off the now-complete inference-efficiency / PTQ arc
(v1170 spec-decode, v1175-v1178 quantization) onto *training dynamics*. Grokking
is one of the few dramatic ML phenomena whose natural habitat *is* toy scale --
it was discovered on small transformers over algorithmic datasets (Power 2022;
Nanda 2023) -- which is the opposite of this session's recurring meta-finding
that toy scale washes effects out.

Design-panel note: the v1179 adversarial design panel (Workflow) could not run
(subagent session-limit), so the five-lens critique was carried out inline and
the resulting de-risked spec is recorded in the version doc. Hyperparameters
follow the canonical full-batch AdamW / high-weight-decay recipe that reliably
groks modular addition at this scale.

Honest-measurement contract (project house rules):

* ``status == "pass"`` IFF the run was VALIDLY MEASURED -- the task is correct,
  the with-decay arm can at least *memorize* the train set (training works), and
  the seed x arm grid is complete. It is NOT gated on whether grokking happens:
  a clean "no grok within budget" is still a pass, just a different verdict.
* The grok step is high-variance and possibly *censored* (a seed may never grok
  within the step budget), so we report ``grok_rate`` and average the grok step
  only over seeds that actually grokked -- never silently dropping censored seeds.
* The weight-decay ablation is PAIRED within a seed (identical init, identical
  split, vary only ``weight_decay``) to isolate the decay effect, and multi-seed
  across seeds for variance.
* A genuine grok requires the *delay* to be real: ``val_at_mem < 0.5`` (validation
  still near chance at the memorization step) and ``grok_gap`` materially larger
  than one eval interval -- this rules out "train and val rose together", which is
  ordinary learning, not grokking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn.functional as F

from minigpt.experiment_utils import mean_std, significant
from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

# Sequence layout: [a, PLUS, b, EQ, c]; the model at the EQ position (index 3)
# predicts the answer token c (index 4). Loss/accuracy are computed there only.
SEQ_LEN = 5
ANSWER_READ_POS = 3
ANSWER_TARGET_POS = 4


@dataclass
class GrokConfig:
    p: int = 97
    # 0.2 puts the task in the grokking regime: the v1179 train_frac sweep showed
    # the memorize->generalize delay grows as the fraction shrinks (0.35 -> gap 200,
    # 0.30 -> 800, 0.25 -> 2100, 0.20 -> ~11300). Above ~0.4 the model generalizes
    # immediately (no delay). 0.2 gives a dramatic, reliable delay with validation
    # still near chance at memorization.
    train_frac: float = 0.2
    n_layer: int = 1
    n_head: int = 4
    n_embd: int = 128
    lr: float = 1e-3
    beta1: float = 0.9
    beta2: float = 0.98
    max_steps: int = 40000
    eval_every: int = 100
    train_acc_thresh: float = 0.99
    val_acc_thresh: float = 0.90
    grok_stop_val: float = 0.95  # early-stop the run once a confirmed grok is this stable
    seeds: tuple[int, ...] = (1337, 1338, 1339, 1340, 1341)
    # First entry is the "with weight decay" arm (the hypothesised driver); last
    # is the paired ablation. decide() compares wds[0] (on) against wds[-1] (off).
    wds: tuple[float, ...] = (1.0, 0.0)


# --------------------------------------------------------------------------
# task: modular addition, full enumeration + deterministic per-seed split
# --------------------------------------------------------------------------
def build_modular_task(p: int) -> torch.Tensor:
    """All ``p**2`` ordered pairs as token sequences ``[a, PLUS, b, EQ, c]``.

    Token ids: ``0..p-1`` are the numbers, ``p`` is ``+`` and ``p+1`` is ``=``;
    the vocabulary size is therefore ``p + 2``. Returns a ``(p**2, SEQ_LEN)``
    long tensor. Pure enumeration -- no RNG, identical across seeds.
    """
    if p < 2:
        raise ValueError("p must be at least 2")
    a = torch.arange(p).repeat_interleave(p)
    b = torch.arange(p).repeat(p)
    c = (a + b) % p
    plus = torch.full_like(a, p)
    eq = torch.full_like(a, p + 1)
    return torch.stack([a, plus, b, eq, c], dim=1)


def split_indices(n: int, train_frac: float, seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Deterministic disjoint (train, val) index split from a seeded permutation.

    Uses its own ``torch.Generator`` so it never perturbs the global RNG stream
    that model initialisation draws from (the init is seeded separately)."""
    if not 0.0 < train_frac < 1.0:
        raise ValueError("train_frac must be in (0, 1)")
    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(n, generator=generator)
    n_train = int(round(train_frac * n))
    n_train = max(1, min(n - 1, n_train))
    return perm[:n_train], perm[n_train:]


def make_grok_model(vocab_size: int, config: GrokConfig) -> MiniGPT:
    """A fresh MiniGPT sized for the grokking task: ``block_size = SEQ_LEN``,
    no dropout (full-batch determinism), learned positional embeddings."""
    return MiniGPT(
        GPTConfig(
            vocab_size=vocab_size, block_size=SEQ_LEN, n_layer=config.n_layer,
            n_head=config.n_head, n_embd=config.n_embd, dropout=0.0, use_rope=False,
        )
    )


# --------------------------------------------------------------------------
# answer-token loss / accuracy
# --------------------------------------------------------------------------
def answer_loss(model: MiniGPT, batch: torch.Tensor) -> torch.Tensor:
    """Cross-entropy on the answer token only (logits at EQ predict c)."""
    logits, _ = model(batch)
    return F.cross_entropy(logits[:, ANSWER_READ_POS, :], batch[:, ANSWER_TARGET_POS])


@torch.no_grad()
def answer_accuracy(model: MiniGPT, batch: torch.Tensor) -> float:
    """Fraction of rows whose argmax answer-token prediction equals c."""
    model.eval()
    logits, _ = model(batch)
    pred = logits[:, ANSWER_READ_POS, :].argmax(dim=-1)
    return (pred == batch[:, ANSWER_TARGET_POS]).float().mean().item()


# --------------------------------------------------------------------------
# one (seed, weight_decay) arm
# --------------------------------------------------------------------------
def train_arm(
    *,
    config: GrokConfig,
    vocab_size: int,
    full_data: torch.Tensor,
    train_idx: torch.Tensor,
    val_idx: torch.Tensor,
    init_state: dict[str, torch.Tensor],
    weight_decay: float,
    device: torch.device,
) -> dict:
    """Train one arm from a fixed initial state and report its grokking metrics.

    The arm starts from ``init_state`` (shared within a seed across arms so the
    only difference between the with/without-decay arms is the decay itself) and
    full-batch AdamW-trains, evaluating train/val answer accuracy every
    ``eval_every`` steps. Stops early once a confirmed grok is stable, otherwise
    runs the full ``max_steps`` budget (so a non-grokking arm is honestly censored
    at the budget rather than declared a grok)."""
    model = make_grok_model(vocab_size, config).to(device)
    model.load_state_dict(init_state)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.lr, betas=(config.beta1, config.beta2), weight_decay=weight_decay
    )
    train = full_data.index_select(0, train_idx).to(device)
    val = full_data.index_select(0, val_idx).to(device)

    curve: list[dict] = []
    t_mem: int | None = None
    t_gen: int | None = None
    val_at_mem: float | None = None
    last_train_acc = 0.0
    last_val_acc = 0.0

    step = 0
    while True:
        if step % config.eval_every == 0 or step == config.max_steps:
            train_acc = answer_accuracy(model, train)
            val_acc = answer_accuracy(model, val)
            curve.append({"step": step, "train_acc": round(train_acc, 6), "val_acc": round(val_acc, 6)})
            last_train_acc, last_val_acc = train_acc, val_acc
            if t_mem is None and train_acc >= config.train_acc_thresh:
                t_mem = step
                val_at_mem = val_acc
            if t_gen is None and val_acc >= config.val_acc_thresh:
                t_gen = step
            if t_gen is not None and val_acc >= config.grok_stop_val:
                break  # confirmed, stable grok -- no need to burn the rest of the budget
        if step >= config.max_steps:
            break
        model.train()
        optimizer.zero_grad(set_to_none=True)
        answer_loss(model, train).backward()
        optimizer.step()
        step += 1

    return {
        "weight_decay": weight_decay,
        "memorized": t_mem is not None,
        "grokked": t_gen is not None,
        "t_mem": t_mem,
        "t_gen": t_gen,
        "grok_gap": (t_gen - t_mem) if (t_gen is not None and t_mem is not None) else None,
        "val_at_mem": val_at_mem,
        "final_train_acc": round(last_train_acc, 6),
        "final_val_acc": round(last_val_acc, 6),
        "steps_run": curve[-1]["step"],
        "curve": curve,
    }


# --------------------------------------------------------------------------
# aggregation + decide
# --------------------------------------------------------------------------
def beats_lower(mean_a: float, std_a: float, mean_b: float, std_b: float) -> bool:
    """True iff ``a`` is significantly LOWER than ``b`` (fewer steps is better) --
    the lower-is-better mirror of :func:`experiment_utils.significant`."""
    return significant(mean_b, std_b, mean_a, std_a)


def arm_aggregate(results: list[dict]) -> dict:
    """Aggregate per-seed arm results, censoring honestly: rates over all seeds,
    grok-step statistics only over the seeds that actually grokked."""
    n = len(results)
    grokked = [r for r in results if r["grokked"]]
    t_gens = [float(r["t_gen"]) for r in grokked]
    gaps = [float(r["grok_gap"]) for r in grokked if r["grok_gap"] is not None]
    vals_at_mem = [float(r["val_at_mem"]) for r in grokked if r["val_at_mem"] is not None]
    final_val = [r["final_val_acc"] for r in results]
    final_train = [r["final_train_acc"] for r in results]

    t_gen_mean, t_gen_std = mean_std(t_gens) if t_gens else (None, 0.0)
    gap_mean, gap_std = mean_std(gaps) if gaps else (None, 0.0)
    val_at_mem_mean, _ = mean_std(vals_at_mem) if vals_at_mem else (None, 0.0)
    final_val_mean, final_val_std = mean_std(final_val)
    final_train_mean, _ = mean_std(final_train)

    return {
        "n": n,
        "n_grokked": len(grokked),
        "grok_rate": (len(grokked) / n) if n else 0.0,
        "mem_rate": (sum(1 for r in results if r["memorized"]) / n) if n else 0.0,
        "t_gen_mean": t_gen_mean,
        "t_gen_std": t_gen_std,
        "grok_gap_mean": gap_mean,
        "grok_gap_std": gap_std,
        "val_at_mem_mean": val_at_mem_mean,
        "final_val_mean": final_val_mean,
        "final_val_std": final_val_std,
        "final_train_mean": final_train_mean,
    }


def decide(config: GrokConfig, arm_results: dict[float, list[dict]]) -> dict:
    """Apply the measurement gates and the verdict ladder.

    Gates (all about VALIDITY, not flattery):
      g0_task_correct  -- the task is well formed (checked by the caller/run).
      g1_memorization  -- the with-decay arm at least memorizes every seed
                          (training works at all; the floor sanity check).
      g2_grid_complete -- every (seed, arm) cell ran.
    ``status == pass`` IFF g0 and g1 and g2. Whether grokking *occurred* sets the
    verdict, never the pass/fail.

    Verdict ladder:
      no_memorization_training_broken     -- g1 failed; the run is not a valid test.
      memorized_no_grok_within_budget     -- with-decay arm mostly never groks in budget.
      grokking_reproduced_wd_driven       -- with-decay groks, ablation essentially never does.
      grokking_reproduced_wd_accelerates  -- both grok, but with-decay groks significantly sooner.
      grokking_reproduced_wd_not_separable-- both grok with no separable step difference.
    """
    wd_on = config.wds[0]
    wd_off = config.wds[-1]
    agg_on = arm_aggregate(arm_results.get(wd_on, []))
    agg_off = arm_aggregate(arm_results.get(wd_off, []))

    g0_task_correct = bool(arm_results.get("_g0_task_correct", True))
    g1_memorization = agg_on["n"] > 0 and agg_on["mem_rate"] >= 0.999 and agg_on["final_train_mean"] >= config.train_acc_thresh
    g2_grid_complete = agg_on["n"] == len(config.seeds) and agg_off["n"] == len(config.seeds)

    # Is the with-decay arm's grok a *genuine delayed* transition?
    delay_real = (
        agg_on["grok_gap_mean"] is not None
        and agg_on["grok_gap_mean"] > config.eval_every
        and agg_on["val_at_mem_mean"] is not None
        and agg_on["val_at_mem_mean"] < 0.5
    )
    reproduced = agg_on["grok_rate"] >= 0.6 and delay_real

    status = "pass" if (g0_task_correct and g1_memorization and g2_grid_complete) else "review"

    if not g1_memorization:
        verdict = "no_memorization_training_broken"
    elif not reproduced:
        verdict = "memorized_no_grok_within_budget"
    elif agg_off["grok_rate"] <= 0.2:
        verdict = "grokking_reproduced_wd_driven"
    elif (
        agg_on["t_gen_mean"] is not None
        and agg_off["t_gen_mean"] is not None
        and beats_lower(agg_on["t_gen_mean"], agg_on["t_gen_std"], agg_off["t_gen_mean"], agg_off["t_gen_std"])
    ):
        verdict = "grokking_reproduced_wd_accelerates"
    else:
        verdict = "grokking_reproduced_wd_not_separable"

    return {
        "status": status,
        "verdict": verdict,
        "gates": {
            "g0_task_correct": g0_task_correct,
            "g1_memorization": g1_memorization,
            "g2_grid_complete": g2_grid_complete,
            "delay_real": delay_real,
            "reproduced": reproduced,
        },
        "agg_on": agg_on,
        "agg_off": agg_off,
    }


# --------------------------------------------------------------------------
# task-correctness check (g0)
# --------------------------------------------------------------------------
def verify_task(full_data: torch.Tensor, p: int) -> bool:
    """Every row satisfies ``c == (a + b) % p`` with the expected op tokens and
    full enumeration of the ``p**2`` pairs."""
    if full_data.shape != (p * p, SEQ_LEN):
        return False
    a, plus, b, eq, c = (full_data[:, i] for i in range(SEQ_LEN))
    if not torch.equal(plus, torch.full_like(plus, p)):
        return False
    if not torch.equal(eq, torch.full_like(eq, p + 1)):
        return False
    return bool(torch.equal(c, (a + b) % p))


# --------------------------------------------------------------------------
# top-level run
# --------------------------------------------------------------------------
def run_grok(*, config: GrokConfig, device: torch.device, generated_at: str | None = None) -> dict:
    """Run the full grokking experiment and return a readability report dict."""
    p = config.p
    vocab_size = p + 2
    full_data = build_modular_task(p)
    g0_task_correct = verify_task(full_data, p)

    arm_results: dict[float, list[dict]] = {wd: [] for wd in config.wds}
    rows: list[dict] = []
    for seed in config.seeds:
        seed_everything(seed)
        train_idx, val_idx = split_indices(full_data.shape[0], config.train_frac, seed)
        init_state = {k: v.detach().clone() for k, v in make_grok_model(vocab_size, config).state_dict().items()}
        for wd in config.wds:
            result = train_arm(
                config=config, vocab_size=vocab_size, full_data=full_data,
                train_idx=train_idx, val_idx=val_idx, init_state=init_state,
                weight_decay=wd, device=device,
            )
            arm_results[wd].append(result)
            rows.append(
                {
                    "seed": seed,
                    "weight_decay": wd,
                    "memorized": result["memorized"],
                    "grokked": result["grokked"],
                    "t_mem": result["t_mem"],
                    "t_gen": result["t_gen"],
                    "grok_gap": result["grok_gap"],
                    "val_at_mem": result["val_at_mem"],
                    "final_train_acc": result["final_train_acc"],
                    "final_val_acc": result["final_val_acc"],
                    "steps_run": result["steps_run"],
                }
            )

    verdict_info = decide(config, {**arm_results, "_g0_task_correct": g0_task_correct})
    agg_on = verdict_info["agg_on"]
    agg_off = verdict_info["agg_off"]
    wd_on, wd_off = config.wds[0], config.wds[-1]

    summary = {
        "p": p,
        "train_frac": config.train_frac,
        "n_layer": config.n_layer,
        "n_embd": config.n_embd,
        "lr": config.lr,
        "weight_decay_on": wd_on,
        "weight_decay_off": wd_off,
        "max_steps": config.max_steps,
        "seeds": len(config.seeds),
        "verdict": verdict_info["verdict"],
        "g0_task_correct": verdict_info["gates"]["g0_task_correct"],
        "g1_memorization": verdict_info["gates"]["g1_memorization"],
        "g2_grid_complete": verdict_info["gates"]["g2_grid_complete"],
        "delay_real": verdict_info["gates"]["delay_real"],
        "grok_reproduced": verdict_info["gates"]["reproduced"],
        "wd_on_grok_rate": agg_on["grok_rate"],
        "wd_on_mem_rate": agg_on["mem_rate"],
        "wd_on_t_gen_mean": agg_on["t_gen_mean"],
        "wd_on_t_gen_std": agg_on["t_gen_std"],
        "wd_on_grok_gap_mean": agg_on["grok_gap_mean"],
        "wd_on_val_at_mem_mean": agg_on["val_at_mem_mean"],
        "wd_on_final_val_mean": agg_on["final_val_mean"],
        "wd_off_grok_rate": agg_off["grok_rate"],
        "wd_off_mem_rate": agg_off["mem_rate"],
        "wd_off_t_gen_mean": agg_off["t_gen_mean"],
        "wd_off_final_val_mean": agg_off["final_val_mean"],
        "boundary": "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
    }

    recommendations = _recommendations(verdict_info)

    return {
        "schema_version": 1,
        "title": "MiniGPT v1179 grokking (delayed generalization)",
        "generated_at": generated_at or utc_now(),
        "status": verdict_info["status"],
        "decision": verdict_info["verdict"],
        "summary": summary,
        "rows": rows,
        "curves": {str(wd): [r["curve"] for r in arm_results[wd]] for wd in config.wds},
        "recommendations": recommendations,
        "csv_fieldnames": [
            "seed", "weight_decay", "memorized", "grokked", "t_mem", "t_gen",
            "grok_gap", "val_at_mem", "final_train_acc", "final_val_acc", "steps_run",
        ],
    }


def _recommendations(verdict_info: dict) -> list[str]:
    verdict = verdict_info["verdict"]
    if verdict == "grokking_reproduced_wd_driven":
        return [
            "Grokking reproduced: train accuracy saturates early, validation generalizes only much later.",
            "Weight decay is the driver -- the wd=0 arm memorizes but (essentially) never groks within budget.",
            "This is a delayed phase transition, not slow co-convergence (val was still near chance at memorization).",
        ]
    if verdict == "grokking_reproduced_wd_accelerates":
        return ["Both arms grok, but weight decay groks significantly sooner -- decay accelerates the transition rather than being strictly necessary at this budget."]
    if verdict == "grokking_reproduced_wd_not_separable":
        return ["Grokking reproduced, but the wd=0 ablation groks at a statistically indistinguishable step -- weight decay's role is not separable at this budget."]
    if verdict == "memorized_no_grok_within_budget":
        return ["The model memorizes the train set but does not generalize within the step budget -- grokking not reproduced here (increase max_steps or revisit hyperparameters)."]
    return ["The with-decay arm failed to even memorize the train set -- training is broken; the run is not a valid grokking measurement."]


__all__ = [
    "GrokConfig", "SEQ_LEN", "ANSWER_READ_POS", "ANSWER_TARGET_POS",
    "build_modular_task", "split_indices", "make_grok_model",
    "answer_loss", "answer_accuracy", "train_arm",
    "beats_lower", "arm_aggregate", "decide", "verify_task", "run_grok",
]
