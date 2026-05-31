# v558 required-term pair constrained decode feasibility 代码讲解

## 本版目标和边界

v557 已经证明 v556 checkpoint 对 `fixed=` 的内部评分偏向 `loss`。v558 要回答一个更工程化的问题：能不能先用 decode 约束作为临时补救，而不是马上改训练目标或模型容量。

本版不训练、不改 checkpoint、不新增正式 generation profile。它只做 feasibility：阻断竞争项首字母，看 fixed/loss 是否能恢复。

## 前置链路

- v555：比较 v552/v554，确认 branch competition。
- v556：tied repair 仍失败。
- v557：teacher-forced forced-choice 显示 `fixed=` 内部偏向 `loss`。

v558 接在 v557 后面，判断 decode-only mitigation 是否值得继续。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_constrained_decode_feasibility.py`
  - 核心诊断模块。
  - 复用 `MiniGPTGenerator` 和 `parse_generation_request`。
  - 对每个 term 运行 default 和 `block_competing_initial`。
- `src/minigpt/model_capability_required_term_pair_constrained_decode_feasibility_artifacts.py`
  - 多格式报告输出。
- `scripts/run_model_capability_required_term_pair_constrained_decode_feasibility.py`
  - CLI 入口。
- `tests/test_model_capability_required_term_pair_constrained_decode_feasibility.py`
  - 用 fake generator 覆盖可行、不可行和输入失败。

## 核心数据结构

每个 case row 记录一次 decode：

```json
{
  "profile_id": "block_competing_initial",
  "term": "fixed",
  "prompt": "fixed=",
  "blocked_token_texts": ["l"],
  "continuation_hit": false,
  "continuation_preview": "01\\npt=01 1 f"
}
```

profile row 汇总命中项：

```json
{
  "profile_id": "block_competing_initial",
  "hit_terms": [],
  "missed_terms": ["fixed", "loss"],
  "pair_full_hit": false
}
```

summary 给出是否值得推广：

```json
{
  "default_hit_count": 1,
  "constrained_hit_count": 0,
  "hit_delta": -1,
  "constrained_pair_full": false,
  "fixed_constrained_hit": false
}
```

## 运行流程

1. CLI 定位 v556 的 `model_capability_required_term_pair_coexistence_refresh.json`。
2. builder 从 replay case rows 取出 `fixed=` 和 `loss=` prompt。
3. default profile 正常生成。
4. `block_competing_initial` profile 对当前 term 的竞争项首字母做 blocked token text：
   - `fixed=` 阻断 `l`。
   - `loss=` 阻断 `f`。
5. 对比 default 与 constrained 的 hit count 和 pair-full。

## 真实结果

真实运行结果：

```text
decision=required_term_pair_constrained_decode_not_feasible
default_hit_count=1
constrained_hit_count=0
hit_delta=-1
constrained_pair_full=False
fixed_constrained_hit=False
```

这比“无提升”更强：约束不仅没有救回 fixed，还破坏了 loss 的默认命中。因此不能把 blocked-token 解码作为当前模型的补救方案。

## 测试覆盖

测试覆盖：

- fake generator 在 constrained profile 下恢复 fixed/loss 时，必须判定 pair-full feasible。
- fake generator 无收益时，必须判定 not feasible。
- 缺 training 或少于两个 term 时，`--require-pass` 失败。
- locator 能从嵌套目录找到 refresh report。
- artifacts 能写出 JSON、CSV、text、Markdown 和 HTML。

## 归档角色

`e/558` 保存 decode-only feasibility 的 JSON、CSV、text、Markdown、HTML、Playwright snapshot 和截图。它是本轮 v551-v558 的收口证据：从 held-out gap 到语料修复、内部评分、解码约束，结论都指向同一件事：seed `1535` 的 equals surface 需要更强的训练目标或模型容量，而不是继续局部 prompt/解码微调。

一句话总结：v558 否定了简单 constrained decoding 的补救路线，为下一阶段转向 objective/capacity 提供了清晰边界。
