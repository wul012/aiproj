# MiniGPT 运行截图和解释归档 f

本目录从 v1098 开始保存模型治理阶段的运行截图和解释，和历史目录 `a/`、`b/`、`c/`、`d/`、`e/` 同级。

- `a/` 保留 v1-v31 的历史运行证据，不迁移。
- `b/` 保留 v32-v68 的历史运行证据，不迁移。
- `c/` 保留 v69-v302 的历史运行证据，不迁移。
- `d/` 保留 v303-v472 的训练治理阶段运行证据，不迁移。
- `e/` 保留 v473-v1097 的模型能力阶段运行证据，不迁移。
- 从 v1098 开始，新的模型治理阶段运行截图和解释写入 `f/`。

目录结构继续沿用旧格式：

```text
f/<version>/图片
f/<version>/解释/说明.md
```

## 当前索引

f/1178/图片
f/1178/解释/说明.md
 -> v1178 PTQ policy sensitivity: reuses v1177 candidate selector over strict/default/aggressive quality budgets. Real v1175 artifact result: `strict_quality -> per_tensor:4b`, `balanced_default -> group32:3b`, `aggressive_compression -> per_channel_row:3b`; `selection_stable_across_profiles=False`. This keeps `group32:3b` as the balanced default recommendation, not an absolute or policy-invariant claim. Evidence includes generated JSON/CSV/text/Markdown/HTML plus Playwright screenshot.

f/1177/图片
f/1177/解释/说明.md
 -> v1177 PTQ deployment candidate selector: consumes the real v1175 PTQ JSON and applies an explicit bounded quality budget (`dCE <= 0.08`, exact-match drop `<= 0.10`, KL `<= 0.10`) to choose the lowest effective-bits candidate. Result: `group32:3b` (`eff_bits=3.5`, `dCE=0.064286`, `KL=0.07137`, `EM drop=0.090555`) is selected; `per_channel_row:3b` is rejected because its exact-match drop exceeds the budget. Boundary remains quality-cost selection only, with no int-kernel speed or memory claim. Evidence includes generated JSON/CSV/text/Markdown/HTML plus Playwright screenshot.

f/1176/图片
f/1176/解释/说明.md
 -> v1176 completion-mask helper dedup: contract-preserving maintenance after v1175 PTQ. New `src/minigpt/completion_masking.py` owns `build_completion_xy` for tokenized `(full, prompt_length)` examples. `distill_common._build_xy` remains a compatibility alias; PTQ v1175 now uses the same helper instead of its local `_padded_xy`. Focused evidence: py_compile passed; completion-mask/distill-common/PTQ tests `26 passed`. Also links `项目通俗说明/README.md` from the root README documentation map.

f/1175/图片
f/1175/解释/说明.md
 -> v1175 post-training weight quantization (PTQ): real RTX 4060 run (5 seeds, 4L/64). Inference-efficiency thread — fake-quantize a trained model's weights (fp32 inference, no int kernels) and measure the held-out CE degradation curve. verdict=per_channel_advantage_not_separable: a sharp cliff exists (lossless ≥6b, usable 3–4b, collapse at 2b) and per-channel/group extend the NOMINAL cliff (per-tensor collapses at 3b CE 0.540, per-channel holds at 0.168) — but the CPU probe's three flattering single-seed claims all dissolve under 5-seed rigor: "per-channel buys a bit" is a wash at matched EFFECTIVE bits (pc 3b CE 0.168 vs pt 4b 0.097, 3.19 vs 4.0 eff-bits), and "attention most sensitive / embedding lossless" vanish (every component ΔCE at 4b is within the fp32 seed-std 0.027; c_attn weight-error ≈ embedding's, KL ~0 = no amplification). The tied embedding is quantized by parameter identity (guarded by a test) so it can't be silently reverted. Weight-only RTN measures the QUALITY cost only — no memory/speed claim at toy scale. The 4th honest-null this session where multi-seed rigor kills a single-seed probe result.

f/1174/图片
f/1174/解释/说明.md
 -> v1174 distillation common helper dedup: contract-preserving maintenance after the v1172 deterministic distillation and v1173 stochastic dark-knowledge pair. New `src/minigpt/distill_common.py` owns completion-token `_build_xy`, Hinton `tau^2` `kl_term`, `shuffle_residual_mass`, `train_student`, `teacher_logit_stats`, and `make_distill_model`. v1172 keeps backward-compatible re-exports; v1173 now imports shared helpers directly instead of depending on a versioned experiment module. Focused evidence: py_compile passed; distillation tests `35 passed`. This version changes the maintenance boundary, not the model-quality claims.

f/1173/图片
f/1173/解释/说明.md
 -> v1173 distillation under aleatoric uncertainty — dark knowledge made real (the mirror of v1172). Real RTX 4060 (5 seeds, K=32). Each context maps to a known multi-modal P_true (Dirichlet, entropy swept) so the teacher is genuinely SOFT (entropy 1.16 ≈ true 1.13), unlike v1172's near-one-hot deterministic teacher; metric = exact KL(P_true‖P_student) at the single stochastic position (EOS-free). verdict=dark_knowledge_is_data_efficiency_under_uncertainty: soft distillation reaches the teacher ceiling (KL 0.050 ≈ teacher 0.041) while hard-label from 1 sample is 4.48; the DARK-KNOWLEDGE term KL(teacher_argmax_hard 3.52) − KL(soft 0.05) = 3.47 dwarfs the data-efficiency term (0.96) and GROWS with entropy (slope lb 3.05 > 0; the data-efficiency confound slope is only 0.30); shuffled_teacher HURTS (2.42, the mirror of v1172 where it was inert); label_smooth only partially helps (1.30). But NOT magic: scratch_many at the teacher's own 400 samples/ctx recovers P (KL 0.047 ≈ soft) — data-efficiency under uncertainty. Entropy calibration: hard/argmax collapse to ~one-hot (bias −1.12), soft/oracle match true entropy (≈0). v1172↔v1173 together answer when distillation helps. KL is lower-is-better → all comparisons via beats_lower.

f/1172/图片
f/1172/解释/说明.md
 -> v1172 knowledge distillation: real RTX 4060 run (5 independent-init seeds). A new capability-transfer axis — a trained teacher (4L/64, EM 0.858) distills into a smaller student via per-token KL, vs hard-label SFT with two disentangling controls (label-smoothing matched to teacher confidence; shuffled-teacher preserving argmax+entropy but destroying class identity) + a matched-FLOPs baseline. On this DETERMINISTIC task the teacher is near-one-hot (max-prob 0.989) so dark knowledge cannot exist by construction. verdict=no_distill_benefit: the CPU probe's flattering +0.058 EVAPORATES and REVERSES under multi-seed independent inits (distill τ1 0.757 vs scratch 0.773; τ2 0.803 > τ1, so the probe's τ ordering flipped — τ is a coupled step-size knob, not a cause), both controls match the baseline, and the Δ(distill−scratch) curve is negative at every student size (the "peaks at mid-capacity" prediction is falsified). The punchline: scratch_long (2485 steps = the teacher-forward compute given back to scratch) reaches 0.949, crushing every distillation arm. Just train the student longer. The design panel + multi-seed + controls + matched-compute caught that the single-seed probe was an artifact.

f/1171/图片
f/1171/解释/说明.md
 -> v1171 maintenance dedup: extract the single-corpus script setup (build corpus → train tokenizer → pad/eos → block-size floor), repeated byte-identically in 5 of 6 run-scripts, into minigpt.script_setup.setup_single_corpus; migrate v1164/v1166/v1168/v1169/v1170 (v1165 dual-corpus left in place). Contract-preserving (RNG-free helper, module signatures untouched → existing tests unchanged & green); adds a regression guard test. Evidence is a before/after structure diagram + the declined-priorities verdict. Crucially, the user's proposed "large" relocations were JUDGED and DECLINED on verified facts (src/minigpt=1226 .py not 2467; tests=665 not 1336; model.py=346 lines; a sampled legacy module is imported by 237 files): archiving/renaming/re-layering 1000+ legacy files would break imports at collection, violate the freeze rule, and erase git/forensic history. The "large" maintenance is in the judgment, not the churn.

f/1170/图片
f/1170/解释/说明.md
 -> v1170 speculative decoding: real RTX 4060 run (3 seeds). Resumes the v1161 inference-efficiency thread — a small draft proposes K tokens, the target verifies them in ONE (K+1)-wide forward, an accept/reject rule keeps the output distributed exactly as target-only decoding. Correctness is VERIFIED on four clauses (verify logits == full forward 1.96e-05 < 1e-4; greedy completions 3600/3600 identical; sampling TV within the noise floor; accept-rule consistent), and acceptance α is graded by draft quality (0.58→0.88→1.0). But the PRIMARY FLOPs-honest metric shows spec processes 1.28× the target positions (a (K+1)-wide verify pays K+1 positions/block regardless of acceptance), total forwards/token ≈2.1 (a tiny draft is NOT free), and wall-clock is 0.55× — SLOWER. At char-toy scale, far below GPU saturation, no wall-clock win is the expected honest result. A design panel re-keyed the gate off greedy-bitwise-identity (unsound: argmax ties) onto the logit invariant before the GPU run.

f/1169/图片
f/1169/解释/说明.md
 -> v1169 reward modeling + best-of-N: real RTX 4060 run (3 seeds). The classic RLHF reward model DPO skips — MiniGPT backbone + scalar head, Bradley-Terry loss. It ranks held-out pairs well (in-dist 0.82, off-dist random-reject 0.64 > chance) but in best-of-N the oracle (any-of-N correct) climbs to 0.54 while RM rerank stays ≈0.10 (≈ a random pick) — the answer is in the pool, the RM can't find it among a policy's own (off-distribution) samples. Reward models are reliable only on-distribution. (HH-RLHF is infeasible at char scale; chose RM instead. Adds MiniGPT.features().)

f/1168/图片
f/1168/解释/说明.md
 -> v1168 DPO+SFT-auxiliary (NLL-regularized DPO): real RTX 4060 run (3 seeds). Adding a chosen-NLL term L = L_DPO + λ·SFT_CE_mean(chosen) RECOVERS the generation vanilla DPO destroys (λ=0 exact-match 0.14 → best λ=1.0 0.68, Δlogp(chosen) −23 → ~0), but only MATCHES plain SFT-on-chosen (0.74) — it does not beat it, and the confusable-suppression edge seen in the tiny probe vanishes at scale. The aux fixes DPO's destructiveness; the preference term adds no capability over plain SFT here (margin ≠ capability). A design panel (session-limited; probe run on the main thread) framed it first.

f/1167/图片
f/1167/解释/说明.md
 -> v1167 experiment_utils dedup: contract-preserving maintenance. Extract the three primitives the SFT/transfer/DPO drivers repeated — mean_std (×3), build_minigpt (×3, incl. inline), clone_state (×2) — into one shared module; migrate v1164/v1165/v1166. _significant stays local to v1166 (single user). Existing module tests unchanged and green = behavior preserved. Evidence is a before/after structure diagram + the green suite.

f/1166/图片
f/1166/解释/说明.md
 -> v1166 DPO-lite preference tuning: real RTX 4060 run (3 seeds). From a weak SFT init, the DPO loss grows the chosen-vs-rejected margin ~6x (14->86) but, because it optimizes a RELATIVE margin, log p(chosen) falls (-26.7) and held-out exact-match REGRESSES 0.59->0.10 — while a matched-compute SFT-on-chosen control rises to 0.76 and the reference/KL term shows no measurable effect at this scale. An adversarial design panel falsified the flattering framings before the GPU run. Preference accuracy up != capability up.

f/1165/图片
f/1165/解释/说明.md
 -> v1165 base->SFT transfer: real RTX 4060 run. Pretraining on {copy,reverse,sort} transfers to a held-out new op (shift-left): at 50 SFT steps pretrained reaches 0.31 vs 0.02 from scratch (~14x), 0.97 vs 0.83 at 1000 — pretraining shifts the SFT curve left (data efficiency). The two-stage recipe, measured.

f/1164/图片
f/1164/解释/说明.md
 -> v1164 SFT instruction-following: real RTX 4060 run. The model follows copy/reverse/sort instructions on unseen inputs (0.79 exact-match, chance ~0.0016) via completion-only loss masking; a step sweep shows the masking advantage is a low-compute accelerant (+0.24 at 150 steps → +0.02 at 1500).

f/1163/图片
f/1163/解释/说明.md
 -> v1163 script_runtime dedup: extract the choose_device helper (14 copies) and the seed triple into one shared module; migrate the 6 capability-pivot scripts. Contract-preserving, full suite 3209 passed. Evidence is a before/after structure diagram + the green test suite.

f/1162/图片
f/1162/解释/说明.md
 -> v1162 learned-vs-RoPE positions beyond trained length: real RTX 4060 5-seed length sweep. Learned beyond-range loss rises +0.12 nats while RoPE stays flat (+0.004); sliding-window learned ties RoPE; both schemes raise identically beyond block_size. Honest scope: tests definedness at longer length, not use of longer context.

f/1161/图片
f/1161/解释/说明.md
 -> v1161 KV-cache: incremental-generation path verified numerically identical to uncached (max logit diff ~1e-6) and ~1.6x faster generating 700 tokens on a real RTX 4060 run.

f/1160/图片
f/1160/解释/说明.md
 -> v1160 RoPE: rotary position embeddings behind a backward-compatible use_rope flag; real RTX 4060 held-out comparison vs learned positions (capability validated, learned slightly ahead at fixed short length).

f/1159/图片
f/1159/解释/说明.md
 -> v1159 train_lm dedup: extract the duplicated training loop from v1156/v1157/v1158 into one shared helper; contract preserved, full suite 3173 passed.

f/1158/图片
f/1158/解释/说明.md
 -> v1158 MiniGPT LoRA domain adaptation: adapt a frozen base to a new sentence structure (shared vocab) on a real RTX 4060 run; LoRA matches full fine-tuning at 7.5% params and stays reversible.

f/1157/图片
f/1157/解释/说明.md
 -> v1157 MiniGPT LoRA held-out generalization eval: validated held-out harness + base/full-finetune/LoRA three-arm comparison on a real RTX 4060 run.

f/1156/图片
f/1156/解释/说明.md
 -> v1156 MiniGPT LoRA fine-tune screenshots and explanation (real RTX 4060 before/after training-loss run).

f/1155/图片
f/1155/解释/说明.md
 -> v1155 unassisted loss suffix repair replay comparison screenshots and explanation.

f/1154/图片
f/1154/解释/说明.md
 -> v1154 unassisted loss suffix repair training run screenshots and explanation.

f/1153/图片
f/1153/解释/说明.md
 -> v1153 unassisted loss suffix repair seed screenshots and explanation.

f/1152/图片
f/1152/解释/说明.md
 -> v1152 unassisted holdout repair partial signal diagnostic screenshots and explanation.

f/1151/图片
f/1151/解释/说明.md
 -> v1151 unassisted holdout repair replay comparison screenshots and explanation.

f/1150/图片
f/1150/解释/说明.md
 -> v1150 unassisted holdout repair training run screenshots and explanation.

f/1149/图片
f/1149/解释/说明.md
 -> v1149 unassisted holdout repair seed corpus screenshots and explanation.

f/1148/图片
f/1148/解释/说明.md
 -> v1148 unassisted holdout repair plan screenshots and explanation.

f/1147/图片
f/1147/解释/说明.md
 -> v1147 decoder-anchor versus unassisted holdout comparison screenshots and explanation.

f/1146/图片
f/1146/解释/说明.md
 -> v1146 decoder anchor local fragment probe screenshots and explanation.

f/1145/图片
f/1145/解释/说明.md
 -> v1145 loss signal bridge and decoder anchor distribution screenshots and explanation.

f/1144/图片
f/1144/解释/说明.md
 -> v1144 real holdout scorecard smoke screenshots and explanation.

f/1143/图片
f/1143/解释/说明.md
 -> v1143 required term coverage real execution screenshots and explanation.

f/1142/图片
f/1142/解释/说明.md
 -> v1142 model capability cadence watch screenshots and explanation.

f/1141/图片
f/1141/解释/说明.md
 -> v1141 model capability regression loop trend screenshots and explanation.

f/1140/图片
f/1140/解释/说明.md
 -> v1140 report loader dedup screenshots and explanation.

f/1139/图片
f/1139/解释/说明.md
 -> v1139 model capability regression follow-up closeout screenshots and explanation.

f/1138/图片
f/1138/解释/说明.md
 -> v1138 model capability regression suite readiness screenshots and explanation.

f/1137/图片
f/1137/解释/说明.md
 -> v1137 model capability regression suite manifest screenshots and explanation.

f/1136/图片
f/1136/解释/说明.md
 -> v1136 model capability regression evidence inventory screenshots and explanation.

f/1135/图片
f/1135/解释/说明.md
 -> v1135 model capability regression plan screenshots and explanation.

f/1134/图片
f/1134/解释/说明.md
 -> v1134 versioned artifact map screenshots and explanation.

f/1133/图片
f/1133/解释/说明.md
 -> v1133 model capability cadence screenshots and explanation.

f/1132/图片
f/1132/解释/说明.md
 -> v1132 publication receipt template and script layer screenshots and explanation.

f/1131/图片
f/1131/解释/说明.md
 -> v1131 project docs readability split screenshots and explanation.

f/1130/图片
f/1130/解释/说明.md
 -> v1130 publication naming readability stopgap screenshots and explanation.

f/1129/鍥剧墖
f/1129/瑙ｉ噴/璇存槑.md
 -> v1129 randomized holdout publication receipt screenshots and explanation.

f/1128/鍥剧墖
f/1128/瑙ｉ噴/璇存槑.md
 -> v1128 randomized holdout publication receipt index review screenshots and explanation.

f/1127/鍥剧墖
f/1127/瑙ｉ噴/璇存槑.md
 -> v1127 randomized holdout publication receipt index screenshots and explanation.

f/1126/鍥剧墖
f/1126/瑙ｉ噴/璇存槑.md
 -> v1126 randomized holdout publication receipt contract-check screenshots and explanation.

f/1125/鍥剧墖
f/1125/瑙ｉ噴/璇存槑.md
 -> v1125 randomized holdout publication receipt screenshots and explanation.

f/1124/鍥剧墖
f/1124/瑙ｉ噴/璇存槑.md
 -> v1124 randomized holdout publication receipt index review screenshots and explanation.

f/1123/鍥剧墖
f/1123/瑙ｉ噴/璇存槑.md
 -> v1123 randomized holdout publication receipt index screenshots and explanation.

f/1122/图片
f/1122/解释/说明.md
 -> v1122 randomized holdout publication receipt contract-check screenshots and explanation.

f/1121/图片
f/1121/解释/说明.md
 -> v1121 randomized holdout publication receipt screenshots and explanation.

f/1120/图片
f/1120/解释/说明.md
 -> v1120 randomized holdout publication receipt index review screenshots and explanation.

f/1119/图片
f/1119/解释/说明.md
 -> v1119 randomized holdout publication receipt index screenshots and explanation.

f/1118/图片
f/1118/解释/说明.md
 -> v1118 randomized holdout publication receipt contract-check screenshots and explanation.

f/1117/图片
f/1117/解释/说明.md
 -> v1117 randomized holdout publication receipt screenshots and explanation.

f/1116/图片
f/1116/解释/说明.md
 -> v1116 randomized holdout publication receipt index review screenshots and explanation.

f/1115/图片
f/1115/解释/说明.md
 -> v1115 randomized holdout publication receipt index screenshots and explanation.

f/1114/图片
f/1114/解释/说明.md
 -> v1114 randomized holdout publication receipt contract-check screenshots and explanation.

f/1113/图片
f/1113/解释/说明.md
 -> v1113 randomized holdout publication receipt screenshots and explanation.

f/1112/图片
f/1112/解释/说明.md
 -> v1112 randomized holdout publication receipt index review screenshots and explanation.

f/1111/图片
f/1111/解释/说明.md
 -> v1111 randomized holdout publication receipt index screenshots and explanation.

f/1110/图片
f/1110/解释/说明.md
 -> v1110 randomized holdout publication receipt contract-check screenshots and explanation.

f/1109/图片
f/1109/解释/说明.md
 -> v1109 randomized holdout publication receipt screenshots and explanation.

f/1108/图片
f/1108/解释/说明.md
 -> v1108 randomized holdout publication receipt index review screenshots and explanation.

f/1107/图片
f/1107/解释/说明.md
 -> v1107 randomized holdout publication receipt index screenshots and explanation.

f/1106/图片
f/1106/解释/说明.md
 -> v1106 randomized holdout publication receipt contract-check screenshots and explanation.

f/1105/图片
f/1105/解释/说明.md
 -> v1105 randomized holdout publication receipt screenshots and explanation.

f/1104/图片
f/1104/解释/说明.md
 -> v1104 randomized holdout publication receipt index review screenshots and explanation.

f/1103/图片
f/1103/解释/说明.md
 -> v1103 randomized holdout publication receipt index screenshots and explanation.

f/1102/图片
f/1102/解释/说明.md
 -> v1102 randomized holdout publication receipt contract-check screenshots and explanation.

f/1101/图片
f/1101/解释/说明.md
 -> v1101 randomized holdout publication receipt screenshots and explanation.

f/1100/图片
f/1100/解释/说明.md
 -> v1100 randomized holdout publication receipt index review screenshots and explanation.

v1098 是文档分流批次，没有运行截图；后续有运行证据时从 `f/<version>` 开始记录。
