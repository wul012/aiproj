# v421 training scale promotion index suite-design carryover 代码讲解

## 本版目标与边界

v421 的目标是把 v420 单个 promotion 报告里的 suite-design regression context 带入 training scale promotion index。promotion index 负责把多个 promotion 聚合成可比较输入，如果这里只过滤 CI regression，就会把带有 benchmark-suite blocker 的 clean-required promotion 误放进 compare inputs。

本版不改训练执行，不改 promotion 生成，不新增新的治理链。它只读取 promotion summary/clean guard 中已有字段，写入 index row、summary、CSV、Markdown、HTML、CLI，并让 compare-input 过滤识别 suite-design regression。

## 前置链路

本版接在 v417-v420 后面：

- v417：training portfolio comparison 产生 dedicated suite-design blocker。
- v418：batch、scale run、comparison、decision、workflow 保留 suite-design regression context。
- v419：execution handoff 消费 suite-design regression，并让 strict handoff guard 识别它。
- v420：promotion acceptance 消费 suite-design regression，并让 strict promotion guard 识别它。
- v421：promotion index 继续聚合这些字段，并从 compare inputs 排除 dirty clean-required promotions。

## 关键文件

### `src/minigpt/training_scale_promotion_index_helpers.py`

`_clean_batch_review_guard()` 新增读取：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`

读取顺序兼容新旧形态：优先 `clean_batch_review_guard` 里的 `handoff_*` 字段，再 fallback 到无前缀字段和 summary 字段。

`_promotion_row()` 把 global suite-design 字段写入每个 promotion row，同时保留 selected 维度：

- `handoff_selected_batch_maturity_suite_design_regression_count`
- `handoff_selected_batch_maturity_suite_design_regression_names`

`clean_requirement_satisfied` 新增 suite-design 条件：

```text
handoff_clean_batch_review_status == clean
and handoff_batch_maturity_ci_regression_count == 0
and handoff_batch_maturity_suite_design_regression_count == 0
```

这意味着 clean-required promotion 即使状态是 `clean`，只要带 suite-design regression，就不会进入 `comparison_inputs`。

`_summary()` 新增聚合：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_selected_batch_maturity_suite_design_regression_total`
- `handoff_batch_maturity_suite_design_regression_names`
- `handoff_selected_batch_maturity_suite_design_regression_names`

`handoff_clean_batch_review_count` 和 `handoff_unclean_batch_review_count` 也同步把 suite-design regression 纳入 clean/unclean 判断。

### `src/minigpt/training_scale_promotion_index.py`

CSV 增加 selected/global suite-design 字段。Markdown summary 和 promotion table 展示 suite-design regression count，HTML stat cards 和 table 也展示同样字段。

这让 reviewer 在浏览 index 页面时可以直接看到：

```text
Comparison ready = 1
Handoff unclean = 1
Handoff suite-design regressions = 1
Suite-design names = suite-index-risk
```

### `scripts/index_training_scale_promotions.py`

CLI stdout 新增：

- `handoff_batch_maturity_suite_design_regression_count`
- `handoff_batch_maturity_suite_design_regression_names`
- `handoff_selected_batch_maturity_suite_design_regression_total`
- `handoff_selected_batch_maturity_suite_design_regression_names`

这样 CI 或 shell-only 检查不打开 JSON，也能解释为什么一个 promoted report 没有进入 compare inputs。

## 核心数据流

本版字段流向是：

```text
training_scale_promotion.summary / clean_batch_review_guard
  -> training_scale_promotion_index_helpers._promotion_row
  -> training_scale_promotion_index_helpers._summary
  -> comparison_inputs filtering
  -> JSON / CSV / Markdown / HTML / CLI evidence
```

selected 维度用于说明被选中 handoff 对应的 suite-design risk；global batch 维度用于判断该 promotion 是否能作为 clean compare input。

## 测试覆盖

`tests/test_training_scale_promotion_index.py` 新增 suite-design regression 测试，覆盖：

- row 级 selected/global suite-design count 和 names。
- summary 级 total 和 name 聚合。
- clean-required promotion 因 suite-design regression 从 compare inputs 排除。
- CSV、Markdown、HTML 都展示 suite-design 字段。
- CLI stdout 输出 suite-design count 和 names。

原有 promoted/review/blocked、suite guard、batch review、clean batch、CI regression、script output 和 helper facade 测试继续通过。

本轮定向验证：

- `python -m pytest tests\test_training_scale_promotion_index.py -q`：`12 passed`
- 语法编译：通过

收口验证：

- `python -m pytest -q`：`713 passed`
- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v421`：`status=pass`
- `git diff --check`：通过

## 运行证据

`d/421` 归档了本版截图和说明：

- `d/421/图片/01-training-scale-promotion-index-suite-design.png`
- `d/421/解释/v421-training-scale-promotion-index-suite-design-evidence.html`
- `d/421/解释/v421-training-scale-promotion-index-suite-design-evidence.json`
- `d/421/解释/v421-training-scale-promotion-index-suite-design-snapshot.md`
- `d/421/解释/说明.md`

截图证明两个 promotion 都是 promoted，但只有一个进入 comparison ready；另一个因为 suite-design regression 被视为 unclean clean-required evidence。

一句话总结：v421 把 suite-design blocker 保留到 promotion index 和 compare-input 过滤层，防止 dirty clean-required promotion 进入后续训练规模对比。
