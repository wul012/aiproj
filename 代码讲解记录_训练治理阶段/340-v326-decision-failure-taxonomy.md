# v326 decision failure taxonomy

## 本版目标和边界

v325 把 threshold profile 下沉到 benchmark scorecard decision artifact。v326 接着补 README 里一直提到的 richer failure taxonomy：让 decision 不只保存 blocker/review 文本，还保存稳定类别。

本版目标：

- 每个 candidate evaluation 输出 `blocker_categories`。
- 每个 candidate evaluation 输出 `review_categories`。
- decision summary 聚合 blocker/review category counts。
- summary 给出 dominant blocker/review category。
- CSV、Markdown、HTML 和 tiny smoke summary 都能展示这些类别。

边界：

- 不改变 promotion decision 规则。
- 不改变模型训练和 benchmark scoring。
- 不改变 threshold profile 的含义。
- 不把 tiny smoke 的 blocked 结果解释为模型能力结论。

## 前置能力

本版基于：

- v322-v324 的 threshold diagnostics。
- v325 的 decision-level threshold profile。
- 既有 generation-quality flag taxonomy 和 scorecard comparison taxonomy。

v326 的定位是把 promotion decision 层也结构化起来，让失败原因可以被 CI 和后续报告消费。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`
  - `_evaluate_run()` 为每个 evaluation 添加 `blocker_categories` 和 `review_categories`。
  - 新增 `_categorize_blockers()` 和 `_categorize_review_items()`。
  - `_summary()` 聚合 `blocker_category_counts`、`review_category_counts`、`dominant_blocker_category`、`dominant_review_category`。
  - `_category_counts()` 只处理非 baseline candidate rows。
  - `BLOCKER_CATEGORY_PRIORITY` 和 `REVIEW_CATEGORY_PRIORITY` 让并列 dominant category 按业务重要性裁决，避免靠字母顺序碰巧决定主失败类型。

- `src/minigpt/benchmark_scorecard_decision_artifacts.py`
  - CSV 输出新增 `blocker_categories` 和 `review_categories`。
  - Markdown summary 输出 dominant blocker/review category。
  - Markdown candidate table 新增 category columns。
  - HTML stats cards 新增 Top blocker / Top review。
  - HTML candidate table 新增 category columns。

- `scripts/run_tiny_scorecard_comparison_smoke.py`
  - top-level smoke summary 转述 `dominant_blocker_category`、`dominant_review_category`、`blocker_category_counts`、`review_category_counts`。
  - 文本 summary 输出 `decision_dominant_*` 和 `decision_*_category_counts`。

- `tests/test_benchmark_scorecard_decision.py`
  - 断言 candidate blocker/review categories。
  - 断言 summary category counts 和 dominant category。
  - 断言 CSV、Markdown、HTML 渲染 taxonomy 字段。

- `tests/test_tiny_scorecard_comparison_smoke.py`
  - 断言 tiny smoke top-level summary 转述 taxonomy。

## 核心类别

blocker categories：

```text
baseline_candidate
missing_rubric
threshold
rubric_regression
overall_regression
other_blocker
```

review categories：

```text
rubric_fail_regression
generation_quality_flag_regression
generation_quality_flag_shift
generation_quality_case_shift
eval_suite_not_ready
case_regression
other_review
```

这些类别来自现有文本规则，不引入新的决策逻辑。

## 数据结构

每个 candidate evaluation：

```json
{
  "blockers": ["rubric_avg_score below 60.0"],
  "blocker_categories": ["threshold"],
  "review_items": [],
  "review_categories": []
}
```

summary：

```json
{
  "blocker_category_counts": {"threshold": 1},
  "dominant_blocker_category": "threshold",
  "review_category_counts": {},
  "dominant_review_category": null
}
```

tiny smoke text：

```text
decision_dominant_blocker_category=threshold
decision_dominant_review_category=None
decision_blocker_category_counts=threshold:1
decision_review_category_counts=
```

## 运行流程

```text
candidate evaluation
  -> blockers / review_items
  -> blocker_categories / review_categories
  -> summary category counts
  -> decision JSON/CSV/Markdown/HTML
  -> tiny smoke summary
```

taxonomy 是证据解释层，不参与 candidate 是否 blocked/review/promote 的判断。
当多个类别计数相同，dominant category 使用显式优先级裁决，例如 blocker 里 `threshold` 高于普通 regression，review 里 `eval_suite_not_ready` 和 `rubric_fail_regression` 高于 generation-quality flag shift。

## 测试覆盖

聚焦测试：

```text
python -B -m unittest tests.test_benchmark_scorecard_decision tests.test_tiny_scorecard_comparison_smoke -v
```

全量验证：

```text
python -B -m unittest discover -s tests -v
python -B scripts/check_source_encoding.py --out-dir runs/v326-source-encoding
python -B -m py_compile src/minigpt/benchmark_scorecard_decision.py src/minigpt/benchmark_scorecard_decision_artifacts.py scripts/run_tiny_scorecard_comparison_smoke.py tests/test_benchmark_scorecard_decision.py tests/test_tiny_scorecard_comparison_smoke.py
git diff --check
```

覆盖点：

- candidate blocker categories。
- candidate review categories。
- summary category counts。
- dominant category。
- CSV header。
- Markdown summary 和 table。
- HTML stats 和 table。
- tiny smoke top-level taxonomy fields。

全量结果是 592 个测试通过；source encoding 没有 BOM、语法错误或 Python 3.11 兼容性错误；`py_compile` 通过；`git diff --check` 返回码为 0，日志里只有 Windows 行尾提示。

## 运行证据

归档位置：

```text
d/326/图片
d/326/解释/说明.md
```

截图证明：

- 聚焦测试通过。
- tiny smoke summary 输出 taxonomy。
- decision Markdown 渲染 taxonomy。
- decision JSON 保存机器可读 taxonomy。
- 全量 unittest、source encoding、py_compile、diff check 都通过。

## 一句话总结

v326 把 benchmark scorecard decision 的失败原因从自然语言文本扩展为稳定 taxonomy，让 CI、报告和人工审阅都能更快判断主失败类型。
