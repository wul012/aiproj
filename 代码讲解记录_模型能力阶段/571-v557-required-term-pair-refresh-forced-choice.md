# v557 required-term pair refresh forced-choice 代码讲解

## 本版目标和边界

v556 的 tied repair 仍然没有恢复 seed `1535` 的 pair-full，`fixed=` 继续生成 loss-like continuation。继续加语料之前，需要判断这是采样/rollout 偏差，还是 checkpoint 内部评分就已经偏向 `loss`。v557 因此新增 refresh forced-choice 诊断。

本版不训练、不改生成配置、不宣称模型质量提升。它只对 v556 已有 checkpoint 做 teacher-forced 候选评分。

## 前置链路

- v555：确认 v552/v554 是 branch competition。
- v556：尝试 tied repair，但 `fixed=` 仍然失败。

v557 承接 v556 的负结果，把问题从“生成文本不对”下探到“候选 continuation 的 NLL 是否偏向错误分支”。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_refresh_forced_choice.py`
  - 核心诊断模块。
  - 输入 pair coexistence refresh report，定位 checkpoint/tokenizer。
  - 对每个 prompt term 评分所有 candidate terms。
- `src/minigpt/model_capability_required_term_pair_refresh_forced_choice_artifacts.py`
  - 多格式输出模块。
  - 将 prompt preference 和 raw score rows 渲染为 CSV、Markdown 和 HTML。
- `scripts/run_model_capability_required_term_pair_refresh_forced_choice.py`
  - CLI 入口。
  - 支持输入 refresh JSON，也支持输入包含 refresh JSON 的目录。
- `tests/test_model_capability_required_term_pair_refresh_forced_choice.py`
  - 用 fake scorer 覆盖 preference collapse 和 internal match 两条关键分支。

## 核心数据结构

`score_rows` 是候选级证据：

```json
{
  "prompt_term": "fixed",
  "prompt": "fixed=",
  "candidate_term": "loss",
  "is_expected_candidate": false,
  "avg_nll": 0.588642,
  "first_token_rank": 1
}
```

`prompt_rows` 汇总每个 prompt 的胜出候选：

```json
{
  "prompt_term": "fixed",
  "expected_term": "fixed",
  "best_candidate_term": "loss",
  "expected_is_best": false,
  "expected_rank": 2,
  "expected_margin_vs_best": 0.010357
}
```

`summary` 给出整体判断：

```json
{
  "expected_best_count": 1,
  "forced_choice_full_match": false,
  "collapse_candidate": "loss",
  "preference_collapse_observed": true
}
```

## 评分流程

1. 读取 refresh report 的 `training.checkpoint_path` 和 `training.tokenizer_path`。
2. 从 `replay_report.case_rows` 中提取 prompt：`fixed=` 和 `loss=`。
3. 对每个 prompt 分别评分候选 `fixed` 和 `loss`。
4. 评分方式是 teacher-forced：逐 token 计算 candidate continuation 的 log probability，得到 `avg_nll`。
5. 每个 prompt 选择 avg NLL 最低的 candidate。
6. 如果两个 prompt 的 best candidate 都塌缩到同一个 term，则输出 preference collapse。

## 真实结果

v557 对 v556 checkpoint 的真实评分：

```text
fixed= best candidate: loss
loss= best candidate: loss
collapse_candidate=loss
expected_best_count=1/2
```

`fixed=` 的差距不大，但方向明确：

```text
loss avg_nll=0.588642
fixed avg_nll=0.598999
margin=0.010357
```

这说明 v556 的 free-generation miss 不是单纯 decode 抽样坏运气，而是模型内部已经更偏向 `loss` continuation。

## 测试覆盖

测试覆盖：

- 当 fake scorer 让 fixed/loss prompt 都偏向 loss 时，必须判定 `preference_collapse`。
- 当每个 prompt 都偏向自己的 expected term 时，必须判定 `internal_match`。
- 无 training 或少于两个 term 时，`--require-pass` 会失败。
- locator 能从目录中找到嵌套 refresh report。
- artifacts 能写出 JSON、CSV、text、Markdown 和 HTML。

## 归档角色

`e/557` 保存 forced-choice JSON、CSV、text、Markdown、HTML、Playwright snapshot 和截图。它是 v556 checkpoint 的只读评分证据，后续版本可以基于它判断是否需要 constrained decoding、目标函数调整或更大 capacity，而不是继续重复类似的语料加权。

一句话总结：v557 证明 seed `1535` 的 equals surface 失败已经进入内部偏好层，下一步应围绕偏好纠偏或约束解码展开。
