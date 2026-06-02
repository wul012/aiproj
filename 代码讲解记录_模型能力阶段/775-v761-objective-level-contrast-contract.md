# v761 objective-level contrast contract 代码讲解

## 本版目标和边界

v761 的目标是把 v760 的 `pair_readiness_objective_level_contrast_plan` 转成真实 contract artifact。v760 只定义了 row family 和 heldout 边界，v761 负责实际展开 26 行训练 rows，并让现有 corpus materializer 能识别这份新 contract。

本版不训练模型，不物化 corpus，不 claim 模型能力提升。它的边界是 contract-only。

## 前置路线

- v759：选择 `objective_level_contrast`。
- v760：定义 4 类 row family 和 26 行训练设计。
- v761：生成实际 contract，并接入 materializer decision/filename mapping。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_contract.py`
  - contract 核心逻辑。
  - 输入 v760 plan。
  - 展开 `OBJECTIVE_LEVEL_CONTRAST_ROW_FAMILIES`。
  - 校验 plan 来源、row count、row family count、fixed/loss branch balance、eval prompt 不泄漏、heldout pair 不泄漏、没有 pipe/equals near-exact prompt surface。

- `src/minigpt/model_capability_required_term_pair_readiness_objective_level_contrast_contract_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - CSV 记录 row family、role、target 和 row count。

- `scripts/run_model_capability_required_term_pair_readiness_objective_level_contrast_contract.py`
  - CLI 入口。
  - 支持输入 v760 JSON 或目录。
  - `--require-pass` 下 contract check 失败返回非 0。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - 新增 ready decision：`pair_readiness_objective_level_contrast_contract_ready`。
  - 新增 contract JSON 文件名：`model_capability_required_term_pair_readiness_objective_level_contrast_contract.json`。
  - 作用是让 v762 可直接复用旧物化器，不需要再写一套训练 corpus 生成逻辑。

- `tests/test_model_capability_required_term_pair_readiness_objective_level_contrast_contract.py`
  - 覆盖 ready contract、错误 plan 失败、heldout prompt 不在 training rows、materializer 能识别目录和多格式输出。

## contract 结构

v761 contract 输出：

```text
decision=pair_readiness_objective_level_contrast_contract_ready
training_row_count=26
row_family_count=4
evaluation_probe_count=3
```

四个 row family：

| family | rows | 作用 |
| --- | ---: | --- |
| objective_header | 6 | 在文本中显式标出 paired required terms 目标 |
| branch_role_contrast | 8 | 平衡 fixed/loss 单分支角色 |
| pair_answer_contrast | 8 | 用 paired objective variants 训练两个 answer terms |
| separator_neutral_answer | 4 | 不用 heldout separator 的 answer 组合 |

## 泄漏和边界检查

v761 明确保留三个 evaluation probes：

```text
fixed=
loss=
fixed=|loss=
```

训练 rows 不允许等于这些 eval prompts，也不允许包含 `|` 或 `=` 这类 near-exact prompt surface。这里的目标是让模型学习 objective-level paired answer，而不是复制刚刚被 v758 关闭的 surface patch 路线。

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_objective_level_contrast_contract.py -q -o cache_dir=runs\pytest-cache-v761-focused
```

结果为 5 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_objective_level_contrast_contract.py e\760\解释\model-capability-required-term-pair-readiness-objective-level-contrast-plan --out-dir e\761\解释\model-capability-required-term-pair-readiness-objective-level-contrast-contract --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Decision pair_readiness_objective_level_contrast_contract_ready`
- `Rows 26`
- `Families 4`
- `Probes 3`
- `exact-heldout-pair: fixed=|loss= -> fixed+loss`

截图位于：

```text
e/761/图片/v761-objective-level-contrast-contract.png
```

## 证据链角色

v761 是 contract 层。它把 v760 的设计计划变成 materializer 可消费的正式数据契约，并且通过映射更新把下一版物化接入旧链路。

一句话总结：v761 生成了 objective-level contrast contract，并证明它可被现有 pair-readiness materializer 接收。
