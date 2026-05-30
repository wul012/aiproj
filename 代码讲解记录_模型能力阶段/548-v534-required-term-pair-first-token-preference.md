# v534 required-term pair first-token preference 代码讲解

## 本版目标和边界

v533 训练成功，但 `fixed:` 和 `loss:` 的 replay continuation 都没有命中目标 term，而是出现类似 `ansssssssss` 的坍缩。v534 不继续训练，而是读取 v533 checkpoint，对两个 prompt 的下一 token logits 做 top-k 排名。

本版不改变模型、不调 generation profile、不重新训练。它只做一个诊断：expected first token `f` / `l` 到底排第几，谁压在它们前面。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_first_token_preference.py`
  - 读取 v533 refresh 报告，加载 checkpoint/tokenizer，计算下一 token probability 和 rank。
- `src/minigpt/model_capability_required_term_pair_first_token_preference_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/run_model_capability_required_term_pair_first_token_preference.py`
  - CLI 入口，支持输入 v533 JSON 或目录。
- `tests/test_model_capability_required_term_pair_first_token_preference.py`
  - 用 fake scorer 覆盖 answer-prefix drift、whitespace-prefix drift、expected-top 和输出渲染。
- `e/534/解释/model-capability-required-term-pair-first-token-preference/`
  - 真实 logits 诊断报告。
- `e/534/图片/01-model-capability-required-term-pair-first-token-preference.png`
  - HTML 报告截图。

## 核心流程

`build_model_capability_required_term_pair_first_token_preference()` 读取 v533 报告中的：

- `training.checkpoint_path`
- `training.tokenizer_path`
- `replay_report.terms`
- `replay_report.case_rows`

然后对每个 term 构造上下文：

```text
prompt = fixed: / loss:
expected_first_text = f / l
```

真实 scorer 会加载 `MiniGPT`：

1. `tokenizer.encode(prompt)` 得到 prompt token ids。
2. 运行 `model(idx)` 得到最后位置 logits。
3. 对 logits 做 softmax。
4. 取 top-k token。
5. 找 expected first token 的 rank 和 probability。

## 关键字段

每个 row 包含：

- `term`
- `prompt`
- `expected_first_text`
- `expected_token_id`
- `expected_rank`
- `expected_probability`
- `top_token_text`
- `top_probability`
- `whitespace_prefix_is_top`
- `answer_prefix_is_top`
- `observed_replay_continuation`

summary 里最重要的是：

```text
expected_top_count
whitespace_prefix_top_count
answer_prefix_top_count
max_expected_rank
```

这些字段把 v533 的生成失败从字符串现象变成了 logits 层面的排序证据。

## 真实结果

真实运行：

```powershell
python -B scripts\run_model_capability_required_term_pair_first_token_preference.py e\533\解释\model-capability-required-term-pair-coexistence-refresh --out-dir e\534\解释\model-capability-required-term-pair-first-token-preference --top-k 8 --force --require-pass
```

结果：

```text
decision=pair_first_token_whitespace_prefix_drift_confirmed
expected_top_count=0
whitespace_prefix_top_count=2
max_expected_rank=8
```

具体到两个 prompt：

```text
fixed: top token 是空格，概率 0.99862206，expected f 排第 6
loss:  top token 是空格，概率 0.99780315，expected l 排第 8
```

所以 v533 的失败不是“模型第一步想输出 a”，而是“模型第一步强烈想输出空格”。`ans...` 是后续生成阶段在空格之后继续坍缩出来的。

## 测试覆盖

单测用 fake scorer 覆盖四类逻辑：

- answer prefix `a` top-ranked 时，decision 是 `pair_first_token_answer_prefix_drift_confirmed`。
- whitespace top-ranked 时，decision 是 `pair_first_token_whitespace_prefix_drift_confirmed`。
- expected `f/l` top-ranked 时，decision 是 `pair_first_token_expected_terms_top_ranked`。
- 输出 writer 生成 JSON、CSV、text、Markdown、HTML。

真实 logits 计算由 `e/534` 的运行证据覆盖。

## 链路角色

v534 是 v533 之后的诊断版。它没有增加模型能力，但把下一步训练方向收窄：不要盲目加 repeat，而是修 corpus 格式偏置，比如减少前导空格答案行、增加 `fixed:fixed` / `loss:loss` 这种 colon-immediate 行。

一句话总结：v534 把 fixed/loss pair 失败定位到第一 token 的空格偏置，为下一次训练改 corpus 提供了明确证据。
