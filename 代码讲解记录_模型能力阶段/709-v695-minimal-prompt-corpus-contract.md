# v695 minimal prompt corpus contract

## 本版目标和边界

v695 的目标是把 v694 readiness 推荐的 `minimal_prompt_equals_surface_objective` 变成真实可用、可检查的语料契约。

本版仍然不训练模型，不生成 checkpoint，不判断模型能力是否提升。它只回答一个问题：如果下一版要训练 minimal-prompt objective，语料输入是否已经满足“不靠 contextual anchor”的边界。

## 前置链路

输入来自 v694：

```text
e/694/解释/model-capability-required-term-pair-minimal-prompt-objective-readiness/
```

v694 已确认：

- minimal prompt objective 可以开启。
- recommended corpus mode 是 `minimal_prompt_equals_surface_objective`。
- 模型质量 claim 仍是 `objective_readiness_only`。

v695 在这个基础上检查推荐语料是否真正注册并可生成。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_objective_corpus.py`
  - 新增 minimal-prompt 语料扩展模块。
  - 暴露 `PAIR_MINIMAL_PROMPT_OBJECTIVE_CORPUS_MODES`、`extend_pair_minimal_prompt_objective_corpus()` 和 mode 判断函数。

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 只做轻量接入。
  - 把新 mode 加入 `PAIR_COEXISTENCE_CORPUS_MODES`，并让 `source_prompts()` 对它返回 `("fixed=", "loss=")`。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_corpus_contract.py`
  - contract builder。
  - 读取 readiness，生成小样本 corpus，检查注册、prompt surface、direct target、prefix span、contextual anchor 和 pair id。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_corpus_contract_artifacts.py`
  - 输出层。
  - 生成 JSON、CSV、text、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_corpus_contract.py`
  - CLI 入口。
  - 支持 readiness JSON 或 readiness 输出目录，支持 `--require-pass`。

- `tests/test_model_capability_required_term_pair_minimal_prompt_corpus_contract.py`
  - focused tests。

## 语料设计

新 mode 的核心不是再加入上下文提示，而是保留最小 inference prompt：

```text
fixed=
loss=
```

语料中包含：

- `fixed=f`
- `fixed=fi`
- `fixed=fix`
- `fixed=fixed`
- `loss=l`
- `loss=lo`
- `loss=los`
- `loss=loss`

它还包含少量文字约束，例如：

```text
minimal prompt objective keeps direct equals prompts.
contextual answer-bearing anchors are not allowed at inference time.
```

这些是训练说明行，不是 inference prompt。contract 会检查高风险 anchor pattern，例如 `fixed=fixed|loss=loss`、`loss=loss|fixed=fixed`、`pair=01`，防止把上一分支的 contextual 成功偷渡进 minimal-prompt 目标。

## 核心检查

`check_rows` 包括：

- `readiness_passed`
- `objective_ready`
- `corpus_mode_registered`
- `source_prompts_are_minimal`
- `fixed_target_present`
- `loss_target_present`
- `fixed_prefix_present`
- `loss_prefix_present`
- `no_contextual_anchor_patterns`
- `no_pair_id`

这里的 `no_contextual_anchor_patterns` 是本版最关键的保护项。它确保下一版训练不再依赖 v679-v693 那条 contextual surface branch。

## 输入输出

输入：

```text
model_capability_required_term_pair_minimal_prompt_objective_readiness.json
```

输出：

```text
model_capability_required_term_pair_minimal_prompt_corpus_contract.json
model_capability_required_term_pair_minimal_prompt_corpus_contract.csv
model_capability_required_term_pair_minimal_prompt_corpus_contract.txt
model_capability_required_term_pair_minimal_prompt_corpus_contract.md
model_capability_required_term_pair_minimal_prompt_corpus_contract.html
```

JSON 是后续训练版本最适合消费的机器证据；HTML 和截图给人工审查使用。

## 测试覆盖

focused tests 覆盖：

- 新 corpus mode 已注册。
- `source_prompts()` 返回 `fixed=` / `loss=`。
- 语料包含 direct target 和 prefix span。
- 语料不包含 contextual paired anchor。
- readiness 正常时 contract pass。
- readiness 推荐未注册 mode 时 contract fail，而不是抛异常。
- 所有输出格式能正常渲染。

## 运行证据

本版证据在：

```text
e/695/解释/model-capability-required-term-pair-minimal-prompt-corpus-contract/
e/695/图片/v695-minimal-prompt-corpus-contract.png
```

证据显示 `contract_ready=True`、`source_prompts=['fixed=', 'loss=']`、`anchor_hit_count=0`。

## 一句话总结

v695 把 minimal-prompt objective 的训练输入从“建议”推进为可注册、可检查、无 contextual anchor 的 corpus contract。
