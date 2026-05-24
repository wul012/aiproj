# v422 promoted training scale comparison suite-design carryover 代码讲解

## 本版目标与边界

v422 的目标是把 v421 promotion index 中的 suite-design regression context 带入 promoted training scale comparison。promoted comparison 是从 promotion index 进入下一轮 baseline/seed 决策前的对比层，如果这里只二次校验 clean status 和 CI regression，就可能被 stale index 误导，把带有 benchmark-suite blocker 的 clean-required promotion 混入对比。

本版不改训练执行，不改 promotion index 生成，不新增新报告。它只读取已有字段，写入 promoted comparison rows、summary、CSV、Markdown、HTML、CLI，并在 comparison 层做 stale-index 二次拦截。

## 前置链路

本版接在 v417-v421 后面：

- v417：training portfolio comparison 产生 dedicated suite-design blocker。
- v418：batch、scale run、comparison、decision、workflow 保留 suite-design regression context。
- v419：execution handoff 消费 suite-design regression，并让 strict handoff guard 识别它。
- v420：promotion acceptance 消费 suite-design regression，并让 strict promotion guard 识别它。
- v421：promotion index 聚合 suite-design regression，并从 compare inputs 排除 dirty clean-required promotions。
- v422：promoted comparison 继续消费和复核这些字段，防止 stale index 漏过滤。

## 关键文件

### `src/minigpt/promoted_training_scale_comparison.py`

`_clean_batch_review_guard()` 新增读取：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`
- `handoff_selected_batch_maturity_suite_design_regression_count`
- `handoff_selected_batch_maturity_suite_design_regression_names`

读取顺序兼容 row、guard 和 summary 三种来源，保持对旧 index JSON 的容错。

`_comparison_exclusion_reasons()` 新增 suite-design 二次校验：

```text
handoff batch suite-design regression count is N
```

这用于 stale index 场景：即使 index row 误标 `promoted_for_comparison=True`，comparison 层仍会根据 suite-design count 排除它。

`_summary()` 新增两组聚合：

- 全量 promotion list：`handoff_batch_maturity_suite_design_regression_count`、names、selected total。
- comparison-ready 子集：`comparison_ready_handoff_batch_maturity_suite_design_regression_count`、names、selected total。

clean/unclean 统计也同步把 suite-design regression 纳入判断：

```text
clean status == clean
and ci regression count == 0
and suite-design regression count == 0
```

`_recommendations()` 在 compared 和 blocked 两种状态下都能解释 suite-design-regressed evidence：它仍保留在 promotion list 中，但被排除在 clean-required promoted comparisons 外。

### `src/minigpt/promoted_training_scale_comparison_artifacts.py`

CSV 新增 selected/global suite-design 字段。Markdown summary 和 promoted input table 展示 suite-design regression count，HTML stat cards 和 table 也展示同样字段。

截图中能看到：

```text
Handoff suite-design regressions = 1
Ready suite-design regressions = 0
```

这说明风险没有丢失，同时没有进入实际比较输入。

### `scripts/compare_promoted_training_scale_runs.py`

CLI stdout 新增：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`
- `handoff_selected_batch_maturity_suite_design_regression_total`
- `comparison_ready_handoff_batch_maturity_suite_design_regression_count`
- `comparison_ready_handoff_batch_maturity_suite_design_regression_names`

这样 CI 或 shell-only 审查不用打开 JSON，也能知道被排除的 promoted 输入是否来自 suite-design blocker。

### `tests/promoted_training_scale_comparison_fixtures.py`

本版顺手把原本膨胀到 900 行以上的 promoted comparison 测试 fixture 拆到独立 helper 文件。这个拆分不改变测试语义，只把 `entry()`、`make_index_tree()`、`scale_run()` 和 JSON 写入辅助函数从主测试文件中移出。

拆分后：

- `tests/test_promoted_training_scale_comparison.py`：666 行
- `tests/promoted_training_scale_comparison_fixtures.py`：237 行

这符合仓库“不制造难维护巨型代码文件”的规则。

## 核心数据流

本版字段流向是：

```text
training_scale_promotion_index.promotions[]
  -> promoted_training_scale_comparison._clean_batch_review_guard
  -> _comparison_exclusion_reasons
  -> promoted rows / summary
  -> JSON / CSV / Markdown / HTML / CLI evidence
```

selected 维度解释被选中 handoff 的 suite-design risk；global batch 维度决定 clean-required promoted input 是否能进入 comparison-ready 子集。

## 测试覆盖

`tests/test_promoted_training_scale_comparison.py` 新增两组测试：

- suite-design context carryover and exclusion：断言 suite-design-regressed clean-required input 被排除，summary 全量计数为 2/1，comparison-ready suite-design count 为 0，CSV/Markdown/HTML/CLI 都展示字段。
- stale index blocking：当 index 误标 suite-design-regressed input 为 compare-ready，comparison 层会二次拦截并让对比 blocked。

原有 suite guard、batch review、clean batch、CI regression、stale CI、blocked input、invalid baseline 和 HTML escape 测试继续通过。

本轮定向验证：

- `python -m pytest tests\test_promoted_training_scale_comparison.py -q`：`13 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`715 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v422`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/422` 归档了本版截图和说明：

- `d/422/图片/01-promoted-training-scale-comparison-suite-design.png`
- `d/422/解释/v422-promoted-training-scale-comparison-suite-design-evidence.html`
- `d/422/解释/v422-promoted-training-scale-comparison-suite-design-evidence.json`
- `d/422/解释/v422-promoted-training-scale-comparison-suite-design-snapshot.md`
- `d/422/解释/说明.md`

截图证明 promoted list 中有 3 个 promoted input，但只有 2 个进入 comparison-ready；suite-design-regressed input 保留为证据并被排除。

一句话总结：v422 把 suite-design blocker 保留到 promoted comparison 和 stale-index 二次过滤层，防止 dirty clean-required promotion 影响后续 baseline 对比。
