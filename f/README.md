# MiniGPT 运行截图和解释归档 f

本目录从 v1098 开始保存模型治理阶段的运行截图和解释，和历史目录 `a/`、`b/`、`c/`、`d/`、`e/` 同级。

## v1270

v1270 将 523 行 `ci_workflow_hygiene.py` 按类型、检查、摘要和公共编排拆分，入口降到 80 行，新模块均低于 240 行。固定输入 canonical report hash 拆分前后完全一致，mypy scope 从 16 收紧到 19，file-size warning count 从 22 降到 21。证据见 `f/1270/解释/`，浏览器核验见 `f/1270/图片/ci-hygiene-type-scope-v1270.png`。

## v1269

v1269 深度压缩 staged ruff 历史债务，baseline 从 545 收紧到 271，净减少 274 条。直接脚本 bootstrap 与兼容 facade 再导出改为精确行级说明，真实无用 import/F811 被修复，`--update-baseline` 增加 fail-closed shrink-only 保护。运行证据见 `f/1269/解释/static-analysis-ratchet/`，浏览器核验见 `f/1269/图片/static-analysis-ratchet-v1269.png`。

## v1268

v1268 收口 Stage-1 外部评审遗留并加固 CI execution economy。主 workflow 只响应 `main` push 与 pull request，tag 不再重复执行同一 commit；setup-python 启用 pip cache，同 ref 的旧 run 可被新提交取消。CI hygiene 将这些配置提升为六条可失败检查。运行证据见 `f/1268/解释/ci-execution-economy/`，浏览器核验见 `f/1268/图片/ci-execution-economy-v1268.png`。

## v1267

v1267 完成 production-excellence A5，新增 A-track final evidence closeout gate。它检查 `docs/aiproj-track-final-evidence.md`、A0-A4 证据文档、no-promotion wording、README/docs 索引和 CI closeout step，防止 A-track 收尾证据在后续阶段静默漂移。运行证据见 `f/1267/解释/aiproj-track-closeout/`，可视化核验见 `f/1267/图片/aiproj-track-closeout-v1267.png`。

## v1266

v1266 完成 production-excellence A4，新增 file-size ratchet。它扫描 `src/`、`scripts/` 和 `tests/` 下的 Python 文件，登记八个历史测试大文件为 no-growth waiver，并在未豁免文件超过 800 行或 waiver 文件继续增长时失败。运行证据见 `f/1266/解释/file-size-ratchet/`，可视化核验见 `f/1266/图片/file-size-ratchet-v1266.png`。

## v1265

v1265 继续 production-excellence A3，新增 artifact schema guard。它用 registry 验证当前 experiment card、dataset card、model card 和 publication receipt 的必需字段、期望值、简单类型与 no-promotion 字段。运行证据见 `f/1265/解释/artifact-schema-guard/`，可视化核验见 `f/1265/图片/artifact-schema-guard-v1265.png`。

## v1264

v1264 启动 production-excellence A3 的 honest-measurement gate。新增 registry 与检查器，验证代表性模型能力治理族是否 cached-artifact-only、no-promotion、seed-policy bounded，并确认源 artifact 与正/负向 contract-test marker 仍存在。运行证据见 `f/1264/解释/model-capability-honest-measurement/`，可视化核验见 `f/1264/图片/honest-measurement-v1264.png`。

## v1263

v1263 完成 production-excellence A2 的覆盖率 floor ratchet。CI 覆盖率门从旧的 `80` 升到 `88.98`，该值来自 v1262 实测 `90.98%` 全量 unittest 覆盖率基线减 2 个百分点。floor 写入 `docs/static-analysis/coverage-floor.json`，并由 CI workflow hygiene 与项目配置测试共同锁定。运行证据见 `f/1263/解释/test-coverage/`，可视化核验见 `f/1263/图片/test-coverage-v1263.png`。

## v1262

v1262 完成 production-excellence A1 的有限范围严格 mypy 门。清单覆盖八个承重文件、四个职责组，并以 `scope_floor=8` 防止范围静默缩小；CI 要求该门位于 ruff 之后、coverage 之前。运行证据见 `f/1262/解释/type-analysis/`，可视化核验见 `f/1262/图片/type-analysis-v1262.png`。

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

f/1261/图片
f/1261/解释/说明.md
 -> v1261 starts A1 from the aiproj production-excellence brief by adopting a staged ruff static-analysis gate. It adds `scripts/check_static_analysis.py`, commits `docs/static-analysis/ruff-baseline.json`, wires the gate into CI and `scripts/check_engineering_health.py`, and extends CI workflow hygiene so static analysis must stay after CI hygiene and before coverage. Real run: `status=pass`, `decision=continue_with_static_analysis_gate`, `current_issue_count=545`, `baseline_issue_count=545`, `new_issue_count=0`, `strict_lint_issue_count=0`, `strict_format_status=pass`. Screenshot: `static-analysis-v1261.png`.

f/1260/图片
f/1260/解释/说明.md
 -> v1260 starts the aiproj production-excellence A-track with A0 census and quick wins. It records the actual CI shape, confirms the latest main CI was green at the start, adds a stdlib-only warning-only archive/runs inventory, writes the first A0 census docs, and refreshes stale START_HERE version text without changing model-capability verdicts or promotion boundaries. Real inventory result: `status=pass`, `decision=archive_runs_inventory_recorded`, `warning_only=True`, `archive_total_mb=390.0008`, `warning_count=0`, largest archive root `e/` at `224.7105 MB`, and `runs/` at `11.349 MB`. Screenshot: `archive-runs-inventory-v1260.png`.

f/1200/图片
f/1200/解释/说明.md
 -> v1200 does WEIGHT DECAY rescue generalization under label noise? -- it REJECTS the noise and reaches early-stopping PARITY (the explicit-regularization complement to v1199's "overparameterization HURTS under label noise"). On v1199's noisy halfspace at a fixed overparameterized width, sweep weight_decay (within-seed paired like v1183) at both eta=0 and eta=0.2, fixed step budget, caching the full test-error trajectory + the FLIP-MASK SPLIT. Result `verdict=wd_equals_early_stopping` (status=pass, 5 seeds): wd DRAMATICALLY improves CONVERGED generalization under noise (test_err 0.368 -> 0.176 at wd=3.0, an INTERIOR optimum -- wd=10 underfits), and the MECHANISM is genuine SELECTIVE NOISE REJECTION -- fit_to_noise collapses 1.0 -> 0.32 while accuracy on the clean-labeled rows stays 0.90 (the wd=10 underfit control collapses to 0.66 = the positive control), a difference-in-differences of 0.24 vs the eta=0 control confirms the gain is NOISE-SPECIFIC. BUT the converged best (0.176) does NOT significantly beat the wd=0 EARLY-STOPPING optimum (0.255) at 5 seeds -> wd reaches early-stopping PARITY at convergence (an oracle-free alternative to early stopping, via noise rejection), not a regime beyond it. Multi-seed deflated the lucky single-seed probe (0.047 -> 0.176), echoing v1199. Designed via a 5-lens adversarial Workflow design panel + a CPU probe; the flip-mask dissociation (argmax-based, immune to the tied-head logit-rescaling confound) is the mechanism proof. Three decide()-threshold artifacts self-caught + fixed on the real Phase-A data (substrate-soundness via the BEST not widest width; convergence via decile DRIFT not jitter; dissociation via a CONTROL-RELATIVE selectivity criterion). Figure: wd dose-response (interior optimum vs the early-stop line) + the noise-rejection dissociation + wd=0-vs-best-wd trajectories + verdict. SCOPE: 1-layer n_head=1 MiniGPT, halfspace L=21, toy scale.

f/1199/图片
f/1199/解释/说明.md
 -> v1199 does a tiny MiniGPT show DOUBLE DESCENT? -- NO (an honest null at toy scale; fresh axis after the induction mechanism closed v1196-98). Double descent (Belkin 2019; Nakkiran 2019) = test error vs capacity is NON-monotone (descends, peaks at the interpolation threshold, descends AGAIN). Substrate = a canonical noisy LINEAR-TEACHER/halfspace over L=21 bits (NOT modular arithmetic, whose grokking dynamics would confound capacity with grok-timing); label noise on a FIXED train set, CLEAN disjoint test. Two arms: MODEL-SIZE (fixed N=256, sweep width, train-to-interpolation on the TRAIN set) and EPOCH-WISE (fixed overparam width, test error vs step). Result `verdict=no_double_descent_monotone` (status=pass, 5 seeds): NO second descent in either arm. Model-size: the BEST generalization is at the UNDERparameterized end and test error rises ~monotonically with width (overparameterization HURTS -- the opposite of a second descent); epoch-wise: test error rises after interpolation to a plateau with NO recovery (single-descent overfitting -> early stopping optimal). The eta=0 control is sound (best clean test err 0.041 << 0.12) and interpolates, so the measurement is VALID; it ALSO shows wide models overfitting clean data, so the epoch-wise rise (0.075) is only partially noise-attributable beyond the control rise (0.051) -> the honest MONOTONE verdict, not a certified signal-before-noise (a clean dip-rise seen in a single-seed probe did NOT survive multi-seed variance). Designed via a 5-lens adversarial Workflow design panel + 4 CPU probes (parity NEVER interpolates noisy labels = dead substrate -> halfspace; absence confirmed across model-size/sample-wise/epoch-wise); a ctrl_ok gate bug (widest vs best width) caught on the real Phase-A data + fixed. Figure: model-size test-err-vs-width (no 2nd descent) + epoch-wise test-err-vs-step (no recovery) + interpolation-threshold + verdict. SCOPE: 1-layer n_head=1 MiniGPT, halfspace L=21, toy scale -- NOT a claim that double descent is absent in large models (well-documented there).

f/1198/图片
f/1198/解释/说明.md
 -> v1198 the induction head's OV circuit is a COPYING circuit (the OV half of the induction mechanism; pairs with v1197's causal QK half to complete the textbook two-part induction-head mechanism, mirroring grokking's weight-level FFT v1188 + causal ablation v1191). Two prongs, BOTH required (disagreement -> review). PRONG 1 weight-level OV copying: M = W_E W_V^T W_O^T W_E^T (Elhage 2021) is diagonal-dominant for induction heads (copy_z +2.52, diag_is_max 0.89) but NOT for the count-matched non-induction L1 control (-1.66, anti-copying) or prev-token heads (-0.45). PRONG 2 activation Direct Logit Attribution (LN-honest): folding each head's residual contribution through the ACTUAL ln_f scale + tied unembed, induction heads add positive logit to the CORRECT answer at inductable positions (DLA_gap +0.566) while the L1 control (-0.043) and prev heads (-0.006) do not. Result `verdict=induction_ov_is_copying_circuit` (status=pass, K=20/T=64, n_head=4, 8 seeds all inducting, base 0.9995, classifiable 7/8, tau-grid 100%). LENS-1 (the tied-embedding Gram confound): the model TIES the unembed to the embedding so the raw Gram W_E W_E^T is itself diagonal-dominant (copy_z +3.83) -> the verdict is PAIRED: the controls share the SAME W_E and differ only in W_V/W_O yet do not copy, proving the induction OV's diagonal is LEARNED by W_V/W_O, not inherited from the Gram. Found via 4 CPU probes (n_head=8 / head size 8 trains induction UNRELIABLY -- the model never crosses the phase transition -> switched to n_head=4, v1196's reliable substrate; DLA threshold calibrated) + a GPU-only torch.arange device bug caught on the first Phase-A run. Figure: induction vs control OV-matrix heatmaps + per-class copy_z/DLA bars + verdict. SCOPE: 2-layer width-64 MiniGPT n_head=4; OV-copying is textbook (Elhage 2021), the NEW bit is the controlled multi-seed, Gram-confound-aware (paired) + DLA-corroborated demonstration. NOT a claim about LLM induction heads.

f/1197/图片
f/1197/解释/说明.md
 -> v1197 induction CIRCUIT causal dissection (mechanistic capstone of the induction axis; v1196 showed induction needs depth, v1197 opens the 2-layer model). On v1196's clean task, heads are classified by attention pattern (prev-token heads = L0 mass on i-1; induction heads = L1 mass on the most-recent-successor position) and causally tested by MEAN-ablation (replace a head's pre-c_proj output with its dataset mean, preserving the LayerNorm operating point; zero-ablation is an agreement check only, since zeroing is an out-of-distribution LayerNorm shock). Result `verdict=circuit_necessary_specific_composed_concentrated` (status=pass, K=20/T=64, 8 seeds, 7 trained): NECESSITY -- ablating ALL prev-token heads -> 0.162, ALL induction heads -> 0.109 (both collapse toward unigram 0.142; zero agrees 0.161/0.108); SPECIFICITY -- a count-matched control (same number of LEAST-prev / LEAST-induction heads) survives 0.972/0.980; COMPOSITION -- ablating prev-token heads drops the induction heads' attention by 0.710 vs only 0.026 for a matched non-prev-L0 control (induction heads READ the prev-token output, beyond a generic LayerNorm shift, re-measured on a SEPARATE batch); REDUNDANCY is ASYMMETRIC (honest nuance) -- induction heads redundant (max single-head drop 0.086 << class drop 0.89) but prev-token heads concentrated (max single drop 0.52, often one dominant head). Verdict invariant across the 0.30-0.50 tau grid. 2 CPU probes (single-head ablation is compensated -> ablate by CLASS) + a 3-lens design panel (mean-ablation not zero; count-matched control; non-prev composition control + separate-batch de-circularization; two-part necessity bar vs the cached unigram floor; degenerate-classification/std==0 guards). Per-seed base gate excludes 1 untrained seed; tau_prev pinned to 0.30 because prev-token detection is sometimes diffuse across several ~0.3 heads. Figure: per-head specialization + necessity/specificity bars + asymmetric redundancy + composition/verdict. SCOPE: 2-layer width-64 MiniGPT n_head=8; circuit + depth are textbook (Anthropic 2022), the NEW bit is the controlled multi-seed redundancy + matched-specificity + mean-ablation demonstration. NOT a claim about LLM induction heads.

f/1196/图片
f/1196/解释/说明.md
 -> v1196 in-context learning / INDUCTION -- does it REQUIRE DEPTH? (fresh axis after the continual-learning arc). CLEAN task: a high-diversity random sequence whose induction target is "the token that MOST-RECENTLY followed the current token" (variable distance, first occurrences masked) -- blocks both the POSITIONAL copy and the FREQUENCY shortcut a shallow model would use. Result `verdict=induction_requires_depth` (status=pass, K=20 T=64, 5 seeds): sweeping width 8->128, a 2-LAYER model learns induction (1.00 from width 24, W*~17) while a 1-LAYER model fails at EVERY width (best 0.43 < success bar S=0.57, even at 128 ~7x the 2-layer threshold). SHORTCUT control: the SAME 1-layer architecture ACES the fixed-offset positional task (1.00) -> its clean-task failure is a content-induction limit, not incapacity. ATTENTION-ONLY arm (MLP zeroed): 2-layer attn-only inducts (0.99) while 1-layer attn-only fails (0.18), and 1-layer WITH its MLP still fails -> the MLP does NOT substitute for depth, so CONSISTENT with the attention-only "needs 2 layers" theorem (not a refutation). CAUSAL swap probe follow-rate 0.91; the 2-layer model shows the composed prev-token->induction attention pattern. Found via 5 CPU probes (each falsified a naive framing: positional shortcut at fixed offset; cyclic free-running task -> frequency exploit) + a 4-lens design panel (unigram gate, W*-ordering not per-width hunting, corrected induction-attention metric, attention-only arm, random-init gate). HONEST: 2-layer UNDER-TRAINS at width>=96 within the fixed budget (an OPTIMIZATION effect -- fresh data ruled out overfitting -- so the verdict uses the converged width range and 1-layer's extended widths only as a one-sided failure bound). Figure: inductable-acc vs width for 1- vs 2-layer + shortcut control + emergence/attention-only + verdict. SCOPE: toy synthetic induction, 1-2 layer MiniGPT WITH MLP + learned abs positions; within-swept-width statement; NOT an LLM in-context-learning claim.

f/1195/图片
f/1195/解释/说明.md
 -> v1195 task-similarity -> catastrophic forgetting (continual-learning axis CAPSTONE). On the v1193 substrate (A=(a+b) consolidated, then B under a TIMES op-token, shared 1-layer transformer, p=23, 5 seeds), the single x-axis is the ANALYTIC output-table overlap of B with A (model-independent |{(a,b):f_B==f_A}|/p^2), varied two ways: a continuous add/mul MIXTURE B_s and a qualitative TYPE family {add_same, add_offset, linear, mul, rand}. Result `verdict=forgetting_governed_by_output_overlap` (status=pass): forgetting is MONOTONE-GRADED in overlap (Spearman -1.0, exact permutation p=0.017, span 0.80) and OPERATION FAMILY IS A RED HERRING -- add_offset (the SAME '+' op, just +c0) forgets 0.991 ~ mul 0.938, both >> the byte-identical add_same (-0.002), and all 3 independent type points lie on the mixture curve (residuals <=0.05), re-confirming v1193's distribution-shift null via a 2nd manipulation. NOT a B-learnedness/drift artifact: overlap out-predicts both (std beta_overlap=-0.98 vs beta_accB=0.0, beta_drift=-0.02), learnedness gated on TRAIN-conflict-cell accuracy (the random mixture partition does not generalize its per-cell split to held-out cells). HONEST deflation: the curve is ~PROPORTIONAL to conflict-fraction (super-linear excess +0.076 < the pre-registered 0.10 bar), so v1193's "catastrophic" forgetting is just the OVERLAP=0 ENDPOINT of a graded overwrite -- the apparent all-or-nothing cliff was an artifact of operation-type changes all landing at overlap~0. Hardened by a 5-lens design panel (analytic-not-measured overlap, materialized (p,p) tables, accB/drift covariates, exclude the definitional overlap=1 point, pre-registered residual/equivalence tests) + 2 CPU probes that falsified the initial structure-reuse hypothesis; one decide() threshold artifact self-caught + fixed from cache. Figure: overlap->forgetting collapse curve (mixture line + type markers + local-overwrite null) + accB confound control + family-red-herring bars. SCOPE: toy modular arithmetic, 1-layer transformer; NOT a claim about instruction-tuned LLM forgetting.

f/1194/图片
f/1194/解释/说明.md
 -> v1194 EWC (parameter anchoring) vs replay (data rehearsal) for catastrophic forgetting, extending v1193 (A=add then B=mul mod 23, shared 1-layer transformer). Compare the two mitigations on their stability-plasticity frontier: sweep each strength knob (EWC lambda / replay buffer k), score best achievable min(acc_A, acc_B). Result `verdict=replay_dominates_ewc` (status=pass, 3 seeds): replay best-min 0.818+/-0.039 vs EWC 0.192+/-0.039 -- replay reaches (acc_A 0.93, acc_B 0.82) while EWC's frontier hugs the axes (protects A OR learns B, never both). EWC got a FAIR shot (gated): anchor demonstrably protects A (max acc_A 0.68 >> naive 0.05), can stay plastic (max acc_B 0.81), lambda swept into the freeze regime -> ewc_all_or_nothing=True is real. Mechanism (ties to v1193): the forgetting is a GLOBAL shift and the most A-important params are the shared/tied number-embedding rows B must overwrite, so a LOCAL diagonal-Fisher anchor can only resist by freezing them (killing B); replay keeps A in the loss without freezing. Honest budget disclosure: replay re-shows stored A rows every step (bigger batch) -> best-min dominance at matched B-step budget, not resource-free Pareto. Hybrid EWC+replay adds nothing on top of replay. Per-example diagonal Fisher; wd=0; tied embedding anchored once. Designed via a 5-lens panel + 4 CPU probes; one decide() absolute-threshold artifact self-caught + fixed from cache (->relative). Figure: stability-plasticity frontier scatter + per-method knob sweeps. NOT a claim EWC is useless in general.

f/1193/图片
f/1193/解释/说明.md
 -> v1193 continual learning / catastrophic forgetting (clean-break fresh axis after calibration). Two op-token-keyed modular tasks share one 1-layer transformer: A=(a+b) mod p, B=(a*b) mod p. Train A to a consolidated plateau, then B; measure A retention. A GLOBAL held-out operand-pair mask quarantines the same (a,b) pairs from A-train/B-train/replay/joint (else A's test operands leak via the shared number-embedding). Result `verdict=catastrophic_forgetting_mitigated_by_replay` (status=pass, p=23): A collapses 0.984->0.041 (~chance 0.043) after learning B (forgetting 0.943, near-instant); replaying A-train examples mitigates as a monotone dose-response (buf128->0.038) while replaying B does not (specific) -- data, not magic. HONEST mechanism: random-label-B (shuffled targets) forgets A just as much (0.937 vs 0.943) -> forgetting is DISTRIBUTION-SHIFT-driven, not B-task-structure-specific (continue-on-A floor ~0 confirms it needs a new distribution); savings slow -> closer to erasure. Two decide() threshold artifacts self-caught + fixed from the cache with zero retrain (g_joint bar; std=0 knife-edge needing a min-effect margin). Phase A trains once + caches, Phase B CPU-only. Designed via a 5-lens panel + 2 CPU probes. Figure: forgetting bars + collapse trajectory + replay dose-response + scope.

f/1192/图片
f/1192/解释/说明.md
 -> v1192 calibration under aleatoric uncertainty + temperature scaling (NEW axis, after grokking closed at v1191). Reuses v1173's stochastic Dirichlet task (known P_true) so calibration is measured against an EXACT oracle; metrics are analytic (oracle ECE exactly 0, avoiding the Jensen bias that makes sampled ECE >0 = oracle sampled floor 0.003). Result `verdict=overconfidence_specifically_corrected_by_temperature` (status=pass): hard-CE n=10 transformer is overconfident (conf 0.559 >> acc 0.442, analytic ECE 0.124 >> floor 0); one global temperature T=1.82 (NLL-fit) reduces ECE to 0.065 (paired Δ0.059±0.029), SPECIFICALLY — ECE-vs-T U-shaped with min at fitted T, wrong T worse (0.141), no help on an already-calibrated model (0.040->0.082). Finite-sample MLE artifact: T->1 as n grows (4.45/1.82/1.24/1.14/1.08). Honest: NLL=entropy+KL so ECE and KL co-move (NO dissociation claimed); calibration adds direction (KL is direction-blind) + an actionable fix. Boundary low-H is the null (gap +0.013, not T-correctable). Phase A trains once + caches logits, Phase B is CPU-only (reuse-cached). Figure: reliability diagram + ECE-vs-T U-curve + samples sweep + scope.

f/1191/图片
f/1191/解释/说明.md
 -> v1191 grokking causal frequency ablation (interpretability capstone): ablate Fourier frequencies in the shipped v1185 checkpoint's tied number-embedding and re-measure held-out accuracy. Result `verdict=dominant_frequencies_sufficient_and_specific_partial_necessity`: keeping ONLY the top-5 freqs [43,3,48,26,44] retains 0.972 (sufficient), removing them is specifically damaging 0.966->0.578 while removing 5 random freqs barely hurts (0.973), but removal doesn't collapse to chance (partial necessity = redundancy). Upgrades v1188/v1190 from correlation to causation. CPU-only, no training. A first-pass decide() threshold under-claimed it as "no dependence" (0.388 drop just under the 0.40 cutoff) — caught and fixed (mirror of the v1183 over-claim). Figure: held-out accuracy across the four interventions.

f/1190/图片
f/1190/解释/说明.md
 -> v1190 grokking logit-frequency alignment: follows the v1188 interpretability axis by aligning embedding dominant frequencies with output-logit frequencies. It loads the shipped v1185 checkpoint, evaluates all `[a,+,b,=]` prompts, builds `L[a,b,y]`, and runs a 2D FFT over `(a,b)`. Ideal addition has diagonal frequency power (`k_a == k_b`); shipped checkpoint result: `status=pass`, `decision=embedding_logit_frequency_alignment_supports_trig_addition`, `logit_diagonal_fraction=0.718712` vs random `0.000122`, ideal `1.0`; logit top-5 frequencies exactly match embedding top-5 `[43,3,48,26,44]`. Boundary: toy-scale single-checkpoint mechanism evidence, not causal ablation or scaling claim.

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
