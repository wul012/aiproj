# v927 randomized holdout publication decision 代码讲解

## 本版目标和边界

v927 的目标是把 v926 的 publication packet review 结果记录成最终 bounded publication decision。

它回答的问题是：

```text
这条 randomized holdout publication 链是否可以被接受为 bounded governance artifact？
```

回答是可以，但范围非常窄：

```text
bounded_randomized_holdout_publication_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不批准 production promotion。
- 不扩大 20-case tiny-checkpoint 结论。

## 前置链路

```text
v926 publication packet review
  -> v927 publication decision
```

v927 的下一步路由到：

```text
index_randomized_holdout_publication_decision
```

## 关键文件

### `src/minigpt/randomized_holdout_publication_decision.py`

核心入口：

```python
build_randomized_holdout_publication_decision(...)
```

输入：

- `publication_review`：v926 review JSON。
- `publication_review_path`：可选源路径。

输出：

```text
status
decision
failed_count
issues
publication_review_path
source_review_summary
source_review
check_rows
final_decision
summary
interpretation
```

### `_checks(...)`

主要检查：

- review 文件存在。
- v926 review status 是 pass。
- review decision ready。
- review summary ready。
- v926 同时在 summary 和 review body 里批准 bounded publication。
- accepted claim 数量为 1。
- blocked claim 数量至少 3。
- allowed use 保持 `bounded_model_capability_governance_only`。
- promotion 和 approved_for_promotion 都是 false。
- review scope 是 `bounded_randomized_holdout_publication_review_only`。
- source failed check count 为 0。

### `final_decision`

通过时：

```text
accepted=True
decision=accept_bounded_randomized_holdout_publication
bounded_publication_accepted=True
promotion_ready=False
approved_for_promotion=False
approved_for_bounded_publication=True
allowed_use=bounded_model_capability_governance_only
decision_scope=bounded_randomized_holdout_publication_only
next_step=index_randomized_holdout_publication_decision
```

这个 final decision 是治理 artifact 的接受，不是模型生产推广。

## Artifact writer

`src/minigpt/randomized_holdout_publication_decision_artifacts.py` 输出：

- JSON：完整 decision。
- CSV：check rows。
- text：命令行摘要。
- Markdown：人工审阅。
- HTML：截图归档。

## CLI

脚本：

```text
scripts/decide_randomized_holdout_publication.py
```

真实运行：

```powershell
python scripts\decide_randomized_holdout_publication.py `
  --publication-review e\926\解释\randomized-holdout-acceptance-publication-packet-review `
  --out-dir e\927\解释\randomized-holdout-publication-decision `
  --require-decision-ready `
  --require-bounded-publication `
  --force
```

## 测试覆盖

新增：

```text
tests/test_randomized_holdout_publication_decision.py
```

覆盖：

1. 干净 v926 review 可以接受 bounded publication。
2. review 不批准 bounded publication 时失败。
3. promotion_ready 被改成 true 时失败。
4. artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

focused 测试：

```text
8 passed
```

## 真实运行证据

真实 v927 读取：

```text
e/926/解释/randomized-holdout-acceptance-publication-packet-review
```

结果：

```text
status=pass
decision=randomized_holdout_publication_decision_accepted
bounded_publication_accepted=True
promotion_ready=False
decision_scope=bounded_randomized_holdout_publication_only
```

截图：

```text
e/927/图片/v927-randomized-holdout-publication-decision.png
```

## 一句话总结

v927 把 randomized holdout publication 链条收成最终 bounded decision，并继续把 production promotion 明确挡住。
