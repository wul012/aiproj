# 1183 · v1171 · MiniGPT 脚本单语料初始化去重（script_setup）+ 否决大规模搬迁

## 目标与边界

到 v1170 已连发 4 个功能版本（v1167 dedup→v1168→v1169→v1170），按 AGENTS.md 节奏做一次保养。用户提了 4 项建议并要求"先判断是否合适再做"。本版的"大"在**判断覆盖面**，不在搬动文件数：先用只读命令核对事实，只做唯一安全、契约保持的抽取，其余按冻结规则诚实否决。

## 入口与核心改动（`src/minigpt/script_setup.py`，新增）

6 个现役 `scripts/run_*` 入口里，**5 个开头是字节级相同**的单语料初始化序列：

```python
corpus = build_sft_corpus(seed=…, ops=…, lengths=…, inputs_per_op_length=…, heldout_ratio=…)
tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
pad_id = tokenizer.encode(PAD)[0]; eos_id = tokenizer.encode(EOS)[0]
block_size = max(16, corpus.max_text_len)
```

抽成单函数 `setup_single_corpus(*, seed, ops, lengths, inputs_per_op_length, heldout_ratio) -> (corpus, tokenizer, pad_id, eos_id, block_size)`，逐字复刻上述序列。**关键签名决策**：返回 `corpus` 与 `tokenizer` 两个对象（而非只返回 id），因为每个脚本对语料的再编码各不相同（`train_examples` / `base_train` / `pref_train_triples` / 奖励模型 pairs / OOD），v1164 还要 `corpus.stats()`；不返回 `corpus_stats`（各脚本字典不同，强行统一会引入分支、非契约保持）；不调 `seed_everything`/`choose_device`、不碰任何全局 RNG。

## 迁移的 5 个脚本

`run_sft_instruction_v1164` / `run_dpo_preference_v1166` / `run_dpo_sft_aux_v1168` / `run_reward_model_v1169` / `run_spec_decode_v1170`：各把内联 5 句换成一次 `setup_single_corpus(...)` 调用 + 一行 import，其余全部不动。**死 import 清理**：v1164/66/68/70 的 `EOS/PAD/build_sft_corpus/CharTokenizer` 迁移后全不再用 → 删；**v1169 保留 `EOS`/`INPUT_ALPHABET`**（OOD 损坏循环仍在用 `e.prompt + corrupted + EOS` 和 `rng.choice(INPUT_ALPHABET)`），只删 `PAD/build_sft_corpus/CharTokenizer`。`build_confusable_preferences`（来自 dpo 模块，非 sft_corpus）保留。

**次序微调（v1166/68/69）**：原先 `build_confusable_preferences(corpus.train,…)` 夹在 `build_sft_corpus` 与 `CharTokenizer.train` 之间；helper 一次做完 corpus+tokenizer，故 `build_confusable_preferences` 挪到 helper **之后**。安全：它只消费 `corpus.train/heldout`，与 tokenizer 互不依赖、均不碰 RNG，重排不改任何值与 RNG 流。

## 明确不在范围

- `run_sft_pretrain_transfer_v1165`：**双语料双种子**（`corpus_seed` 与 `corpus_seed+1`、联合 tokenizer、`block_size=max(16, base, downstream)`、`base_stream` 预训练），无法折进单语料 helper，整体留在脚本内。
- 所有 `src/minigpt/*_v11xx.py` 模块体：per-seed 循环、report 字典骨架、init 快照、子种子派生公式（`20_000+seed*13+budget` 等）、`_param_l2_delta`（仅 2 处，未达 3+）、NaN-safe round、`corpus_stats or {}`——均 RNG-stream 耦合或 duck-typed 或未达阈值，留原地。
- `experiment_utils.py`/`script_runtime.py`/`sft_corpus.py`/`model.py` 等不动；新 helper 因依赖 `sft_corpus`+`tokenizer`（而 experiment_utils 刻意不 import 它们），单独成 `script_setup.py`。

## 据事实否决的提案（核对后高风险、违冻结规则）

只读命令实测：src/minigpt **1226** 个 .py（非 2467）、tests **665**（非 1336）、`model.py` **346 行**（远未到 500-800）、抽样历史模块被 **237 文件** import。据此否决：P1 搬 1000+ 文件到 archive/（237 import 在收集阶段即失败）、P2 改名截断（切断 git 历史 + 抹掉递归命名 bug 取证痕迹）、P3.2 拆 model.py（仅 346 行）、P3.3 重排子包（重写 1226 模块+665 测试的全部 `minigpt.*` import）、P4 archive 后跑 --cov（依赖被否决的 P1，得假阴性）。冻结规则原文："历史长命名/目录只止血、索引、说明、低风险桥接，不做无兼容迁移的改名搬迁。"

## 契约保持论证 + 测试

(1) 纯代码搬移、逐字复刻；(2) 不碰全局 RNG（`build_sft_corpus` 内部自带 `random.Random(seed)`，`CharTokenizer.train` 纯函数），`seed_everything`/`choose_device` 仍在各 main() 且顺序不变 → 后续各 seed 模型初始化权重逐位不变；(3) 模块 `run_*` 签名未动，单元测试不经过脚本 main() 初始化块；(4) 次序微调值中性。新增 `tests/test_script_setup.py`：回归守卫（helper == 旧 inline，对 vocab/pad/eos/block_size/`corpus.stats()`/逐样本编码逐一相等）、确定性、block_size 下限与跟随。5 脚本 `py_compile` 通过、无残留死 import、v1164 端到端 smoke 正常。全量 pytest 保持绿（仅 +3 测试，既有测试不改 = 行为未变的证据）。

## 一句话总结

核对事实后，本次保养只做了唯一安全的脚本单语料初始化抽取（`script_setup.setup_single_corpus`，契约保持 + 回归守卫），并据冻结规则与 237 文件 import 耦合**诚实否决**了会破坏导入/历史/测试的大规模搬迁、改名与重排——保养的价值在判断，不在churn。
