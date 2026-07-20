"""v1193: CONTINUAL LEARNING / catastrophic forgetting (a genuinely fresh axis).

The grokking arc (v1179-91) studied ONE task's learning dynamics; v1192 (calibration)
turned out adjacent to v1173's KL. This is the clean break the project picked next:
SEQUENTIAL multi-task interference. Two distinguishable modular ops on a SHARED 1-layer
transformer, keyed by an op token so a joint model CAN learn both:

    Task A: [a, PLUS,  b, EQ, c],  c = (a+b) mod p
    Task B: [a, TIMES, b, EQ, c],  c = (a*b) mod p

Train A to a consolidated plateau, then train B; measure how much A's held-out accuracy
collapses. The design panel (5-lens) + a CPU probe hardened it against the obvious traps:

* GLOBAL held-out pair-mask: the SAME (a,b) operand-pairs are quarantined from A-train,
  B-train, the replay buffer AND joint-train. Otherwise A's "test" operands leak in via
  B-train (the number-embedding rows are shared / tied), making forgetting uninterpretable.
* CONSOLIDATION: A is trained to a SUSTAINED plateau (acc held W evals), not a fragile
  first-crossing -- else "forgetting" just measures "A was never really learned".
* FIXED B-budget: retention is read at a fixed number of B steps across all seeds/arms.
* Controls that make the claim honest: continue-on-A (no shift -> ~0 forgetting, the floor),
  random-label-B (same inputs, shuffled targets -> does B's STRUCTURE matter, or is it
  generic gradient drift?), a replay buffer-size dose-response (re-exposure, the v1173
  "not magic" framing), a WRONG-replay specificity gate (replaying B must NOT protect A),
  the multitask JOINT upper bound, and a savings/relearning probe (erasure vs masking).
* "Catastrophic" is gated on MAGNITUDE: the verdict says "catastrophic" only when A drops
  to near chance (~1/p); milder drops are relabeled (no v1183-style adjective inflation).

``status=="pass"`` certifies a VALID measurement (A consolidated, B genuinely learned
above its majority-class prior, tasks jointly learnable, no operand leak), NEVER a
flattering result. Training (Phase A) is split from analysis (Phase B): Phase A logs all
accuracies/trajectories to a cache; the verdict re-derives with zero retrain.

Scope: toy modular-arithmetic generalization on a 1-layer transformer; this says nothing
about instruction-tuned LLM forgetting.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import torch

from minigpt.continual_v1193_decision import (
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    decide_continual,
)
from minigpt.continual_v1193_report import build_report
from minigpt.experiment_utils import mean_std
from minigpt.grok_v1179 import ANSWER_READ_POS, ANSWER_TARGET_POS, SEQ_LEN, answer_accuracy, answer_loss
from minigpt.model import GPTConfig, MiniGPT

OPS = {
    "add": lambda a, b, p: (a + b) % p,
    "mul": lambda a, b, p: (a * b) % p,
    "sub": lambda a, b, p: (a - b) % p,
}


@dataclass
class ContinualConfig:
    p: int = 23
    task_a: str = "add"
    task_b: str = "mul"
    train_frac: float = 0.8
    n_layer: int = 1
    n_head: int = 4
    n_embd: int = 128
    lr: float = 1e-3
    beta1: float = 0.9
    beta2: float = 0.98
    weight_decay: float = 0.5
    consolidate_max_steps: int = 6000
    plateau_acc: float = 0.98
    plateau_hold: int = 5
    eval_every: int = 50
    b_budget: int = 1500
    b_eval_every: int = 100
    replay_buffer_sizes: tuple[int, ...] = (0, 8, 32, 128)   # 0 == naive floor
    savings_ks: tuple[int, ...] = (1, 2, 5, 10, 20, 50, 100, 200, 400)
    joint_max_steps: int = 6000
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    # decide() thresholds (justified, multi-signal -- never a single cutoff)
    catastrophic_chance_mult: float = 3.0   # "catastrophic" if acc_A_after_B < mult / p
    b_learn_margin: float = 0.25            # learnable: acc - majority_prior >= margin (B and joint)
    floor_tol: float = 0.05                 # continue-on-A forgetting must be <= this (the floor)
    min_reduction: float = 0.05             # a forgetting reduction must beat this margin AND the
                                            # combined std to count (guards the std==0 knife-edge:
                                            # identical-across-seeds runs give std 0, so a trivial
                                            # ~0.01 gap would otherwise read as "significant")


# --------------------------------------------------------------------------- task + mask
def op_token(cfg: ContinualConfig, which: str) -> int:
    """Op token id: PLUS=p, TIMES=p+1, EQ=p+2 (vocab p+3)."""
    return {"A": cfg.p, "B": cfg.p + 1}[which]


def vocab_size(cfg: ContinualConfig) -> int:
    return cfg.p + 3


def eq_token(cfg: ContinualConfig) -> int:
    return cfg.p + 2


def pair_masks(cfg: ContinualConfig, seed: int) -> tuple[torch.Tensor, torch.Tensor]:
    """A single GLOBAL boolean (train, test) split over all p^2 (a,b) pairs, shared by
    BOTH ops and every arm so the test operands are quarantined from all training."""
    n = cfg.p * cfg.p
    g = torch.Generator().manual_seed(seed)
    perm = torch.randperm(n, generator=g)
    k = int(round(cfg.train_frac * n))
    k = max(1, min(n - 1, k))
    train = torch.zeros(n, dtype=torch.bool)
    train[perm[:k]] = True
    return train, ~train


def build_op(cfg: ContinualConfig, which: str, mask: torch.Tensor) -> torch.Tensor:
    """Rows ``[a, op, b, EQ, c]`` for op ``which`` over the (a,b) pairs selected by ``mask``."""
    p = cfg.p
    op_name = cfg.task_a if which == "A" else cfg.task_b
    a = torch.arange(p).repeat_interleave(p)[mask]
    b = torch.arange(p).repeat(p)[mask]
    c = OPS[op_name](a, b, p)
    opid = torch.full_like(a, op_token(cfg, which))
    eq = torch.full_like(a, eq_token(cfg))
    return torch.stack([a, opid, b, eq, c], dim=1)


def verify_no_leak(train_rows: torch.Tensor, test_rows: torch.Tensor) -> bool:
    """No (a,b) operand-pair appears in BOTH a train stream and the test set."""
    tr = {(int(r[0]), int(r[2])) for r in train_rows}
    te = {(int(r[0]), int(r[2])) for r in test_rows}
    return tr.isdisjoint(te)


def majority_prior(rows: torch.Tensor, p: int) -> float:
    """Largest single-class fraction among the answer tokens (the trivial-shortcut floor)."""
    counts = torch.bincount(rows[:, ANSWER_TARGET_POS], minlength=p)
    return float(counts.max().item() / rows.shape[0])


# ------------------------------------------------------------------------------- training
def make_model(cfg: ContinualConfig) -> MiniGPT:
    return MiniGPT(GPTConfig(vocab_size=vocab_size(cfg), block_size=SEQ_LEN, n_layer=cfg.n_layer,
                             n_head=cfg.n_head, n_embd=cfg.n_embd, dropout=0.0, use_rope=False))


def _opt(model: MiniGPT, cfg: ContinualConfig):
    return torch.optim.AdamW(model.parameters(), lr=cfg.lr, betas=(cfg.beta1, cfg.beta2),
                             weight_decay=cfg.weight_decay)


def _step(model: MiniGPT, opt, batch: torch.Tensor) -> None:
    model.train()
    opt.zero_grad(set_to_none=True)
    answer_loss(model, batch).backward()
    opt.step()


def consolidate(cfg: ContinualConfig, a_train: torch.Tensor, a_test: torch.Tensor,
                seed: int, device) -> tuple[dict, float, int]:
    """Train A to a SUSTAINED plateau (acc_A_test >= plateau_acc held plateau_hold evals).
    Returns (state_dict, plateau_acc_value, steps)."""
    torch.manual_seed(seed)
    model = make_model(cfg).to(device)
    opt = _opt(model, cfg)
    a_train = a_train.to(device)
    a_test = a_test.to(device)
    hold = 0
    step = 0
    while step < cfg.consolidate_max_steps:
        for _ in range(cfg.eval_every):
            _step(model, opt, a_train)
            step += 1
        hold = hold + 1 if answer_accuracy(model, a_test) >= cfg.plateau_acc else 0
        if hold >= cfg.plateau_hold:
            break
    return copy.deepcopy(model.state_dict()), answer_accuracy(model, a_test), step


def train_phase(cfg: ContinualConfig, init_state: dict, b_train: torch.Tensor, *,
                a_test: torch.Tensor, b_test: torch.Tensor, replay_train: torch.Tensor | None = None,
                replay_k: int = 0, seed: int = 0, device=None) -> dict:
    """From a consolidated init, train the fixed B-budget on ``b_train`` (optionally mixing
    ``replay_k`` sampled rows of ``replay_train``); log acc_A trajectory at b_eval_every."""
    model = make_model(cfg).to(device)
    model.load_state_dict(init_state)
    opt = _opt(model, cfg)
    b_train = b_train.to(device)
    a_test = a_test.to(device)
    b_test = b_test.to(device)
    if replay_train is not None:
        replay_train = replay_train.to(device)
    gen = torch.Generator(device="cpu").manual_seed(seed + 7)
    traj = []
    for s in range(cfg.b_budget):
        batch = b_train
        if replay_train is not None and replay_k > 0:
            idx = torch.randint(0, replay_train.shape[0], (replay_k,), generator=gen).to(device)
            batch = torch.cat([b_train, replay_train.index_select(0, idx)], dim=0)
        _step(model, opt, batch)
        if s % cfg.b_eval_every == 0:
            traj.append(round(answer_accuracy(model, a_test), 6))
    return {"accA_after_B": answer_accuracy(model, a_test),
            "accB_after_B": answer_accuracy(model, b_test),
            "trajA": traj, "state": copy.deepcopy(model.state_dict())}


def savings_probe(cfg: ContinualConfig, forgotten_state: dict, a_train: torch.Tensor,
                  a_test: torch.Tensor, target: float, seed: int, device) -> list:
    """Relearn A from a forgotten model; record (cumulative k-steps, acc_A). Fast recovery
    = representational masking; slow (≈ fresh) = erasure."""
    model = make_model(cfg).to(device)
    model.load_state_dict(forgotten_state)
    opt = _opt(model, cfg)
    a_train = a_train.to(device)
    a_test = a_test.to(device)
    curve = []
    done = 0
    for k in cfg.savings_ks:
        while done < k:
            _step(model, opt, a_train)
            done += 1
        curve.append([int(k), round(answer_accuracy(model, a_test), 6)])
    return curve


def run_phase_a(cfg: ContinualConfig, device) -> dict:
    """The single training pass: all arms x seeds -> a cache of accuracies/trajectories
    (no verdict logic here, so Phase B can re-derive verdicts with no retrain)."""
    chance = 1.0 / cfg.p
    seeds = cfg.seeds
    per = {"accA_plateau": {}, "naive": {}, "random_label_B": {}, "continue_on_A": {},
           "joint": {}, "savings": {}, "wrong_replay": {}}
    replay = {bs: {} for bs in cfg.replay_buffer_sizes}
    b_majority = None
    leak_ok = True

    for seed in seeds:
        train_mask, test_mask = pair_masks(cfg, seed)
        A_tr = build_op(cfg, "A", train_mask)
        A_te = build_op(cfg, "A", test_mask)
        B_tr = build_op(cfg, "B", train_mask)
        B_te = build_op(cfg, "B", test_mask)
        if b_majority is None:
            b_majority = majority_prior(B_tr, cfg.p)
        leak_ok = leak_ok and verify_no_leak(A_tr, A_te) and verify_no_leak(B_tr, A_te)

        state, plateau, _ = consolidate(cfg, A_tr, A_te, seed, device)
        per["accA_plateau"][seed] = plateau

        # replay sweep (0 == naive). keep naive's forgotten state for the savings probe.
        for bs in cfg.replay_buffer_sizes:
            out = train_phase(cfg, state, B_tr, a_test=A_te, b_test=B_te,
                              replay_train=A_tr if bs > 0 else None, replay_k=bs, seed=seed, device=device)
            replay[bs][seed] = {"accA_after_B": out["accA_after_B"], "accB_after_B": out["accB_after_B"],
                                "trajA": out["trajA"]}
            if bs == 0:
                per["naive"][seed] = replay[bs][seed]
                per["savings"][seed] = savings_probe(cfg, out["state"], A_tr, A_te, plateau, seed, device)

        # random-label-B null (same B inputs, shuffled targets) -> structure vs drift
        gen = torch.Generator().manual_seed(seed + 101)
        B_rand = B_tr.clone()
        B_rand[:, ANSWER_TARGET_POS] = B_tr[:, ANSWER_TARGET_POS][torch.randperm(B_tr.shape[0], generator=gen)]
        per["random_label_B"][seed] = {"accA_after_B": train_phase(
            cfg, state, B_rand, a_test=A_te, b_test=B_te, seed=seed, device=device)["accA_after_B"]}

        # continue-on-A floor (no distribution shift -> ~0 forgetting)
        per["continue_on_A"][seed] = {"accA_after_B": train_phase(
            cfg, state, A_tr, a_test=A_te, b_test=B_te, seed=seed, device=device)["accA_after_B"]}

        # wrong-replay specificity (replay B-train, not A -> must NOT protect A)
        per["wrong_replay"][seed] = {"accA_after_B": train_phase(
            cfg, state, B_tr, a_test=A_te, b_test=B_te, replay_train=B_tr, replay_k=cfg.replay_buffer_sizes[-1],
            seed=seed, device=device)["accA_after_B"]}

        # multitask joint upper bound (fresh model on A_tr + B_tr)
        torch.manual_seed(seed)
        jm = make_model(cfg).to(device)
        jopt = _opt(jm, cfg)
        both = torch.cat([A_tr, B_tr], dim=0).to(device)
        A_te_d = A_te.to(device)
        B_te_d = B_te.to(device)
        js = 0
        hold = 0
        while js < cfg.joint_max_steps:
            for _ in range(cfg.eval_every):
                _step(jm, jopt, both)
                js += 1
            hold = hold + 1 if (answer_accuracy(jm, A_te_d) >= cfg.plateau_acc and
                                answer_accuracy(jm, B_te_d) >= cfg.plateau_acc) else 0
            if hold >= cfg.plateau_hold:
                break
        per["joint"][seed] = {"accA": answer_accuracy(jm, A_te_d), "accB": answer_accuracy(jm, B_te_d)}

    return {"config": {"p": cfg.p, "task_a": cfg.task_a, "task_b": cfg.task_b, "train_frac": cfg.train_frac,
                       "b_budget": cfg.b_budget, "replay_buffer_sizes": list(cfg.replay_buffer_sizes),
                       "seeds": list(seeds), "weight_decay": cfg.weight_decay},
            "chance": chance, "b_majority_prior": b_majority, "leak_free": leak_ok,
            "accA_plateau": per["accA_plateau"], "naive": per["naive"], "random_label_B": per["random_label_B"],
            "continue_on_A": per["continue_on_A"], "joint": per["joint"], "savings": per["savings"],
            "wrong_replay": per["wrong_replay"], "replay": replay}


# ------------------------------------------------------------------------------- analysis
def _forgetting(plateau: dict, after: dict, seeds) -> tuple[float, float]:
    """Per-seed forgetting = plateau_acc_A - acc_A_after_B; returns (mean, std)."""
    return mean_std([plateau[s] - after[s]["accA_after_B"] for s in seeds])


def summarize(cache: dict, cfg: ContinualConfig | None = None) -> dict:
    """Aggregate the per-seed cache into mean±std signals decide()/build_report read."""
    cfg = cfg or ContinualConfig()
    seeds = [s for s in cache["accA_plateau"]]
    chance = cache["chance"]
    plateau = cache["accA_plateau"]

    naive_forget = _forgetting(plateau, cache["naive"], seeds)
    cont_forget = _forgetting(plateau, cache["continue_on_A"], seeds)
    rand_forget = _forgetting(plateau, cache["random_label_B"], seeds)
    wrong_forget = _forgetting(plateau, cache["wrong_replay"], seeds)

    replay_forget = {int(bs): _forgetting(plateau, cache["replay"][bs], seeds)
                     for bs in cache["replay"]}
    bs_sorted = sorted(replay_forget)
    replay_max_bs = bs_sorted[-1]

    # savings: average recovery curve + the k to recover to plateau-0.05
    plateau_m = mean_std([plateau[s] for s in seeds])[0]
    recov_ks = []
    for s in seeds:
        rk = next((k for k, a in cache["savings"][s] if a >= plateau[s] - 0.05), None)
        recov_ks.append(rk)
    recov_clean = [k for k in recov_ks if k is not None]
    recovered_k = max(recov_clean) if len(recov_clean) == len(seeds) else None

    joint_accA = mean_std([cache["joint"][s]["accA"] for s in seeds])
    joint_accB = mean_std([cache["joint"][s]["accB"] for s in seeds])
    naive_accB = mean_std([cache["naive"][s]["accB_after_B"] for s in seeds])
    naive_accA_after = mean_std([cache["naive"][s]["accA_after_B"] for s in seeds])

    # mean trajectory of acc_A through the B phase (naive)
    trajs = [cache["naive"][s]["trajA"] for s in seeds]
    L = min(len(t) for t in trajs)
    traj_mean = [round(float(sum(t[i] for t in trajs) / len(trajs)), 5) for i in range(L)]

    return {
        "seeds": seeds, "chance": chance, "b_majority_prior": cache["b_majority_prior"],
        "leak_free": cache["leak_free"],
        "accA_plateau": mean_std([plateau[s] for s in seeds]),
        "naive_forget": naive_forget, "naive_accA_after_B": naive_accA_after, "naive_accB_after_B": naive_accB,
        "continue_on_A_forget": cont_forget, "random_label_B_forget": rand_forget,
        "wrong_replay_forget": wrong_forget,
        "replay_forget": replay_forget, "replay_max_bs": replay_max_bs,
        "joint_accA": joint_accA, "joint_accB": joint_accB,
        "recovered_k": recovered_k, "plateau_m": plateau_m, "traj_mean": traj_mean,
        "config": cache["config"],
    }


# Verdict vocabulary and report assembly live in focused pure modules.
def decide(result: dict, cfg: ContinualConfig | None = None) -> dict:
    """Apply the pre-registered continual-learning verdict ladder."""
    return decide_continual(result, cfg or ContinualConfig())


__all__ = [
    "ContinualConfig", "OPS", "op_token", "vocab_size", "eq_token", "pair_masks", "build_op",
    "verify_no_leak", "majority_prior", "make_model", "consolidate", "train_phase", "savings_probe",
    "run_phase_a", "summarize", "decide", "build_report", "REVIEW_VERDICTS", "PRIMARY_VERDICTS",
]
