# v667 required-term pair v630 constrained decode feasibility

## 本版目标和边界

v667 接在 v666 resume branch closeout 后，验证一个更克制的问题：不继续训练、不改 checkpoint，只用 constrained decode 能否让 v630 的 generation anchor 变成 fixed/loss pair-full。

本版不声称模型能力提升。它是 decode-only feasibility check。

## 前置链路

- v630 是当前 generation pair-full 锚点，但 forced-choice 内部不完全对齐。
- v660-v666 证明 naive checkpoint continuation 没有把 v630 变成 aligned pair-full。
- v666 将下一步指向 constrained decode 或显式 dual-objective boundary。

## 运行命令

```powershell
python -B scripts\run_model_capability_required_term_pair_constrained_decode_feasibility.py e\630\解释\model-capability-required-term-pair-loss-internal-joint-cycle-seed-3535 --out-dir e\667\解释\model-capability-required-term-pair-v630-constrained-decode-feasibility --max-new-tokens 12 --temperature 0.8 --top-k 2 --device cpu --require-pass --force
```

## 输出结构

报告包含：

- `training`: checkpoint/tokenizer 路径和存在性。
- `terms`: fixed/loss 两个 prompt 与 generation seed。
- `case_rows`: default 和 block competing initial 两种 profile 下的生成结果。
- `profile_rows`: 每种 profile 的 hit terms、missed terms、pair_full_hit。
- `summary`: default/constrained hit count、hit delta、best profile。

## 核心结果

- `decision=required_term_pair_constrained_decode_partial_gain`
- `default_hit_count=0`
- `constrained_hit_count=1`
- `hit_delta=1`
- `constrained_pair_full=False`
- `fixed_constrained_hit=False`

constrained decode 只帮助 `loss=` 命中 loss，`fixed=` 仍然没有命中 fixed。因此它不能作为 promotion profile，只能作为一条 partial-gain 证据。

## 链路角色

v667 的价值在于把“是不是只要换解码就行”这件事做成 evidence。答案是：当前 profile 不够。

下一步如果继续模型能力线，应该关注：

- fixed constrained miss 的具体 token path。
- 是否需要显式 dual-objective boundary，而不是单纯 block competing initial。
- 是否需要把 generation pair-full 和 internal pair-full 的目标拆成可组合约束。

## 运行证据

- JSON/CSV/text/Markdown/HTML：`e/667/解释/model-capability-required-term-pair-v630-constrained-decode-feasibility/`
- 解释：`e/667/解释/说明.md`
- 截图：`e/667/图片/v667-v630-constrained-decode-feasibility.png`

一句话总结：v667 证明 constrained decode 有单侧收益，但还不能把 v630 变成 fixed/loss pair-full。
