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

f/1189/图片
f/1189/解释/说明.md
 -> v1189 CI unittest portability fix: repairs the v1186-v1188 GitHub Actions failure where `tests/test_grok_predict_v1186.py` imported `pytest` for a skip marker even though CI runs stdlib `unittest discover` without pytest. Replaced the marker with `unittest.skipIf`, added local `src/` path injection, and repaired the engineering-stage code-explanation README index for v1185-v1188. Boundary: CI/test portability and documentation index repair only; no checkpoint, model behavior, or interpretability-claim changes.

f/1188/图片
f/1188/解释/说明.md
 -> v1188 grokking mechanistic interpretability (NEW axis): FFT of the learned number-embeddings to test the Fourier-structure hypothesis for HOW the grokked model computes `a + b mod 97`. Paired grokked (wd=1) vs memorized-not-grokked (wd=0) vs random-init, 3 seeds. Real RTX 4060 result: `verdict=fourier_structure_explains_generalization` — top-5 frequency power fraction `0.307±0.004` (grokked) > `0.150±0.002` (memorized) > `0.120±0.001` (random); only the generalizing model develops the structure. Honestly qualified: significant + generalization-linked but MODEST (top-5 ≈ 31%, 34/48 freqs for 90%), not the ultra-sparse attention-only basis. Shipped v1185 checkpoint carries it (top-5 0.305, dom freq 43). Figure: three-arm spectra + concentration bar. Boundary: toy-scale embedding-Fourier-structure interpretability only.

f/1187/图片
f/1187/解释/说明.md
 -> v1187 report-check scaffolding dedup (maintenance, no behavior change): the four grokking-audit modules (v1180/81/82/84) each re-implemented three byte-identical pieces — the check-row builder `_check`, the `failures` collector, and `resolve_exit_code`. Extracted into `src/minigpt/report_check_common.py` (`check_row`/`collect_failures`/`resolve_exit_code`); each module imports them, keeping public names. Contract-preserving: the four audit test files are unchanged and still green (`25 passed` focused) plus single-source identity guards. PTQ checks (v1177/78) deliberately left untouched. The figure is the shared-module → four-callers schematic.

f/1186/图片
f/1186/解释/说明.md
 -> v1186 grokking checkpoint inference demo (use, not just save): a minimal `load_checkpoint + predict` API that computes `a + b (mod 97)` from the shipped v1185 `.pt`. Loaded from disk (CPU): `train_acc=1.0`, `heldout_acc=0.966` over 7527 unseen pairs (re-derived independently of the v1185 training run), demo pairs all correct (`36+37=73`, `96+96=95`, `40+80=23`), `verdict=grokking_checkpoint_usable`. The figure is a 97×97 correctness map of the learned modular-addition table (train cells light, held-out-correct green, 256 errors red). Boundary: toy-scale single-task inference demo, not a scaling claim.

f/1185/图片
f/1185/解释/说明.md
 -> v1185 canonical grokking checkpoint (productize, not sweep): freezes the default recipe (`a + b = c (mod 97)`, 1-layer MiniGPT, AdamW lr=1e-3 wd=1.0 — the v1183 interior optimum — train_frac=0.2, seed=1337), trains one model to grok, and saves a self-contained checkpoint (`grok_checkpoint_v1185.pt`, ~835KB: weights + meta). Real RTX 4060 result: memorize @ step 100, generalize @ step 11400, held-out accuracy 0.966 on 7527 unseen pairs, `roundtrip_logits_identical=True`, `verdict=canonical_grokking_checkpoint_ready`. The figure is the single train/val curve (memorize-first-then-generalize); a demo reloads the checkpoint standalone and proves generalization. Boundary: toy-scale single-task canonical checkpoint, not a scaling claim.

f/1184/图片
f/1184/解释/说明.md
 -> v1184 grokking weight-decay law contract check: consumes the real v1183 `grok_wd_law_v1183.json` and reconstructs the interior-optimum claim from dose rows and seed rows. Result: `status=pass`, `decision=wd_law_interior_optimum_reconstructed`, `failed_count=0`, threshold wd=0.3, fastest interior wd=1.0, fastest gap=11640 steps, low-end and high-end censoring both true. The strongest dose wd=3.0 still memorizes 5/5 but groks 0/5, preventing the old monotone-acceleration over-claim from reappearing. Boundary: artifact reconstruction only, no training rerun and no broader scaling claim.

f/1183/图片
f/1183/解释/说明.md
 -> v1183 grokking weight-decay dose-response: sweeps weight decay {0,0.1,0.3,1.0,3.0} on `a + b = c (mod 97)` (5 seeds, paired init+split, reuses the v1179 training primitive) to turn the binary "weight decay drives grokking" into a dose-response. Real RTX 4060 result: `verdict=wd_dose_response_interior_optimum` — grok_rate 0/0.2/1.0/1.0/0.0, fastest grok at wd=1.0 (t_gen 14920±5944), threshold wd=0.3; the strongest decay wd=3.0 still memorizes 5/5 but groks 0/5 even at 100k steps (over-regularization, not budget). A first-pass `monotone_acceleration` over-claim was caught and `decide` fixed to detect the high-end censoring. The figure is a dual-axis t_gen-vs-wd plot. Boundary: toy-scale single-task dose-response, not a scaling claim.

f/1182/图片
f/1182/解释/说明.md
 -> v1182 grokking paired contrast: consumes the real v1181 phase report and collapses each seed's weight-decay/no-decay rows into one counterfactual row. Result: `status=pass`, `decision=grokking_weight_decay_pair_contrast_consistent`, `pair_count=5`, `matched_memorization_count=5`, `on_delayed_grok_count=5`, `off_memorized_censored_count=5`, `no_decay_censored_count=5`, `mean_final_val_gain=0.8003984`, `min_final_val_gain=0.753687`, `mean_steps_saved_by_grok_stop=24760.0`, `longest_delay_seed=1341`, `largest_final_val_gain_seed=1339`. Boundary: paired phase contrast only, no training rerun. Evidence includes generated JSON/CSV/text/Markdown/HTML plus Playwright screenshot.

f/1181/图片
f/1181/解释/说明.md
 -> v1181 grokking trajectory phases: consumes the real v1179 `grok_v1179.json` curves and compresses each seed/arm into a phase row. Result: `status=pass`, `decision=grokking_phase_profile_consistent`, `curve_count=10`, `wd_on_delayed_grok_count=5`, `wd_off_memorized_censored_count=5`, `paired_phase_separation_count=5`, `wd_on_low_plateau_rate_mean=0.8321336571672611`, `wd_on_min_gap=10400.0`, `wd_on_max_gap=25100.0`, `longest_delay_seed=1341`. Boundary: curve phase compression only, no training rerun and no broader model-quality claim. Evidence includes generated JSON/CSV/text/Markdown/HTML plus Playwright screenshot.

f/1180/图片
f/1180/解释/说明.md
 -> v1180 grokking evidence check: consumes the real v1179 `grok_v1179.json` and reconstructs the claim from rows instead of trusting the summary text. The check verifies paired seed/arm grid completeness, weight-decay arm memorization + delayed generalization, no-decay ablation non-grokking, mean delay gap, low validation accuracy at memorization, summary/row rate agreement, and the toy-scale boundary. Result: `status=pass`, `decision=grokking_evidence_claim_reconstructed`, `failed_count=0`, `wd_on_mean_gap=14780.0`, `wd_on_mean_val_at_mem=0.14693769365549086`. Evidence includes generated JSON/CSV/text/Markdown/HTML plus Playwright screenshot.

f/1179/图片
f/1179/解释/说明.md
 -> v1179 grokking (delayed generalization): a 1-layer MiniGPT on `a + b = c (mod 97)`, train_frac=0.2, paired weight_decay=1.0 vs 0.0 over 5 seeds. Real RTX 4060 result: `verdict=grokking_reproduced_wd_driven` — with weight decay all 5 seeds memorize by ~step 100 then generalize at ~step 14880 (validation near chance during the gap); without weight decay they memorize identically but never generalize within 40k steps. The figure is the canonical accuracy-vs-log-step grokking curve; evidence includes generated JSON/CSV/text/Markdown/HTML. Boundary: toy-scale single-task phenomenon reproduction, not a scaling claim.

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
