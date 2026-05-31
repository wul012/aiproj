# v569 required-term pair route held-out replay

## 本版目标和边界

v569 接在 v568 route decision 之后，目标是验证被选中的 `v562-loss-balanced` 是否能从源 prompt 转移到 held-out prompt surfaces。

这一版不训练新模型，不新增语料模式，也不扩大模型规模。它只读取 v568 的路线决策，定位 v562 的真实 checkpoint，然后用已有 generation profile replay 做只读复核。

## 前置能力

- v567：比较 v562/v564/v566，证明 first-token density 是覆盖迁移。
- v568：选择 `v562-loss-balanced`，并停止继续调 first-token density。
- generation profile replay：已有的 checkpoint replay 能力，可以对固定 prompt、term 和 profile 组合生成 case rows。

v569 的输入是：

```text
e/568/解释/model-capability-required-term-pair-first-token-route-decision/model_capability_required_term_pair_first_token_route_decision.json
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_route_heldout_replay.py`
  - 主 builder。
  - 负责解析 route decision、读取 selected source report、筛选 pair-full seed、构造 held-out replay source report。
- `src/minigpt/model_capability_required_term_pair_route_heldout_replay_artifacts.py`
  - 写出 JSON、CSV、text、Markdown、HTML。
  - 同时把每个 held-out replay 的 sidecar report 落盘。
- `scripts/run_model_capability_required_term_pair_route_heldout_replay.py`
  - 命令行入口。
- `tests/test_model_capability_required_term_pair_route_heldout_replay.py`
  - 保护 ready/not-ready、失败输入、sidecar 输出和目录定位。

## 核心流程

v569 的 builder 做了五步：

1. 读取 v568 route decision。
2. 从 `selected_route.source_path` 找到 v562 稳定性报告。
3. 筛出 `pair_full_observed=True` 的 seed report。
4. 为每个 held-out prompt spec 构造一个 generation profile replay source report。
5. 汇总每个 spec 是否 pair-full。

默认 prompt specs 来自旧 seed-config held-out replay：

```text
colon-spaced: fixed:  / loss:
equals:       fixed= / loss=
arrow:        fixed -> / loss ->
```

## 输出字段

主报告包含：

- `selected_route`
  - v568 选出的 route。
- `selected_source_report`
  - v562 源稳定性 JSON。
- `replay_rows`
  - 每个 prompt spec 的 pair-full 结果。
- `replay_reports`
  - 每个 spec 的原始 generation profile replay。
- `summary`
  - `heldout_pair_full_count`、`heldout_pair_full_rate`、`heldout_all_pair_full`。
- `interpretation`
  - 说明本版只支持 targeted held-out claim，不支持稳定模型能力 claim。

## 真实运行结果

```text
decision=required_term_pair_route_heldout_replay_ready
heldout_pair_full_count=3
row_count=3
heldout_all_pair_full=True
```

这意味着 v562 seed `1535` 在三种 held-out prompt surfaces 上都能保持 fixed/loss pair-full。

## 测试覆盖

新增测试并没有 mock 掉 builder 逻辑，只替换底层 generator：

- fake pair-full generator 用来验证 ready 分支。
- fake fixed-only generator 用来验证 not-ready 分支。
- 失败输入测试验证 `--require-pass` 的语义。
- 输出测试验证 sidecar generation profile replay 会落盘。

这保护的是 v569 的核心契约：路线选择报告必须能被转成真实 replay 输入，且 replay 结果必须有可追溯 sidecar。

## 链路角色

v569 是 v568 的执行层。v568 说“先 replay held-out equals-surface prompts”，v569 把它变成可运行脚本、真实 checkpoint replay 和可截图报告。

## 一句话总结

v569 证明 `v562-loss-balanced` 的 seed `1535` 不只是源 prompt 记忆，而是在三种 held-out prompt surfaces 上保持了 targeted pair-full 信号。
