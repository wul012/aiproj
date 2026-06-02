# v762 objective-level contrast corpus materialization 代码讲解

## 本版目标和边界

v762 的目标是把 v761 contract 物化为训练 corpus 和 heldout eval fixture。因为 v761 已经把新 decision/filename 注册进 materializer，v762 不需要新增物化器代码，而是复用 `run_model_capability_required_term_pair_readiness_corpus_materialization.py`。

本版不训练模型，不解释模型质量，只输出 data-artifact-only 证据。

## 前置路线

- v761：生成 `pair_readiness_objective_level_contrast_contract_ready` contract。
- v762：读取 v761 contract，生成 `pair_readiness_training_corpus.txt` 和 `pair_readiness_heldout_eval_fixture.json`。

## 关键文件和产物

- `scripts/run_model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 复用已有 CLI。
  - 输入 v761 contract 目录。
  - 输出 JSON/CSV/TXT/Markdown/HTML、训练 corpus 和 heldout fixture。

- `e/762/解释/model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization/pair_readiness_training_corpus.txt`
  - 最终训练文本。
  - 由 26 行 contract rows 重复 320 次得到 8320 行。

- `e/762/解释/model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization/pair_readiness_heldout_eval_fixture.json`
  - 训练后 replay 使用的 heldout fixture。
  - 保留 `fixed=`、`loss=`、`fixed=|loss=` 三类 probes。

## 输入输出结构

输入来自 v761：

```text
decision=pair_readiness_objective_level_contrast_contract_ready
training_row_count=26
row_family_count=4
evaluation_probe_count=3
```

v762 输出：

```text
decision=pair_readiness_corpus_materialized
training_line_count=8320
evaluation_probe_count=3
materialization_ready=True
```

## 检查含义

materializer 继续执行通用检查：

- source contract status 必须是 `pass`。
- source contract decision 必须在 ready contract decisions 集合里。
- repeat 必须大于 0。
- training rows 必须存在。
- heldout pair probe 不得作为 training row。
- heldout pair probe 不得出现在最终 corpus line 中。

v762 的价值在于证明 v761 的新 contract 不是孤立报告，而是能进入旧训练链路。

## 测试和验证

本轮相关测试覆盖：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_contract.py tests\test_model_capability_required_term_pair_readiness_corpus_materialization.py -q -o cache_dir=runs\pytest-cache-v761
```

v762 真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_corpus_materialization.py e\761\解释\model-capability-required-term-pair-readiness-objective-level-contrast-contract --out-dir e\762\解释\model-capability-required-term-pair-readiness-objective-level-contrast-corpus-materialization --repeat 320 --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_corpus_materialized`
- `Train lines 8320`
- `Eval probes 3`
- corpus preview。

截图位于：

```text
e/762/图片/v762-objective-level-contrast-corpus-materialization.png
```

## 证据链角色

v762 是 data input 层。它让 v763 可以做真实 tiny training，而不是直接从 contract 跳到训练结论。

一句话总结：v762 证明 objective-level contrast contract 可以稳定生成训练 corpus 和 heldout eval fixture。
