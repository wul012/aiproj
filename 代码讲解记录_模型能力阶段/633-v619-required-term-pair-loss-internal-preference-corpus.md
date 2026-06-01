# v619 required-term pair loss-internal-preference corpus

## 本版目标和边界

v619 承接 v618 的结论：contrast-free 路线没有 pair-full，forced-choice 也没有 full internal match，因此下一步不再继续加 contrast-free 变体，而是设计 loss-internal-preference objective。

本版不训练新模型，不声明模型能力提升；它只把新 objective 语料模式接入现有 tiny 训练入口。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_corpus.py
e/619/解释/loss-internal-preference-objective-corpus-contract/
```

## 核心设计

`PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES` 定义三种可训练语料模式：

- `loss_internal_preference_repair`：把 `forced choice loss= prefers loss` 这类偏好行写进语料。
- `loss_internal_first_token_repair`：优先强化 `loss=` 后应该出现 `l`。
- `loss_internal_ranked_choice_repair`：把 `candidate loss rank 1` 这种 teacher-forced 排序信号转成训练文本。

这些模式都保持 `fixed=` / `loss=` 的 prompt surface，不引入 `pair=01`，避免回到旧的 pair-id 泄漏。

## 链路角色

`model_capability_required_term_pair_coexistence_corpus.py` 把新模式加入 `PAIR_COEXISTENCE_CORPUS_MODES`，并让 `source_prompts()` 对这些模式返回 `("fixed=", "loss=")`。

这意味着后续版本可以直接复用 `scripts/run_model_capability_required_term_pair_coexistence_refresh.py` 做真实训练和 replay，不需要重复造训练框架。

## 测试覆盖

新增测试覆盖：

- 三种模式已经注册到全局 coexistence corpus mode 列表。
- 三种模式都使用 `fixed=` / `loss=`。
- internal preference、first-token、ranked-choice 的关键语料行真实生成。
- 语料不包含 `pair=01`。

## 运行证据

`e/619/解释/loss-internal-preference-objective-corpus-contract/` 保存 JSON/CSV/text/Markdown/HTML contract。

`e/619/图片/v619-loss-internal-preference-corpus-contract.png` 是 Playwright MCP 对 HTML 的截图，证明 contract 页面可读且字段完整。

## 一句话总结

v619 把 v618 的“停止 contrast-free”转成可训练的 loss-internal-preference objective 入口。
