# v276 promoted seed handoff clean batch-review gate

## 本版目标和边界

v276 的目标是把 v275 已经写入 promoted next-cycle seed 的 clean batch-review evidence 继续传到 promoted seed handoff 报告。

v275 解决的是“seed 是否知道 selected promoted baseline 来自 clean-required handoff，以及 dirty clean-required promoted inputs 是否被排除”。v276 解决的是下一层问题：当 seed 被拿去验证或执行下一轮 `plan_training_scale.py` 命令时，handoff 报告也必须能看到同一组 clean batch-review 字段。

本版不做新的训练，不修改模型结构，不改变 `--execute` 是否执行 plan command 的行为，也不扩大 clean-evidence requirement 的判定范围。它只把已经存在的 clean batch-review 证据投影到 seed handoff summary、artifact、CLI 和 recommendation。

## 前置链路

本版接在 v273-v275 后面：

- v273：promoted comparison 消费 promotion index clean batch-review guard，并排除 dirty clean-required promoted inputs。
- v274：promoted decision 继续保留 selected handoff 的 clean batch-review status，并拒绝 dirty clean-required baseline candidates。
- v275：promoted seed 把 selected clean batch-review requirement/status 和 clean/unclean counts 写入 `baseline_seed.handoff_clean_batch_review`。
- v276：promoted seed handoff 从 `baseline_seed.handoff_clean_batch_review` 读取这些字段，继续公开到下一轮 plan handoff 的证据层。

因此 v276 的角色不是新建 gate，而是让 gate evidence 在 seed handoff 层不断链。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_review.py`

这个文件是 seed handoff 的审查 helper 层。

本版新增 `build_seed_handoff_clean_batch_review_summary(baseline)`：

- 输入：promoted seed JSON 里的 `baseline_seed`。
- 读取：`baseline_seed.handoff_clean_batch_review`。
- 输出：一组扁平 summary 字段：
  - `selected_handoff_require_clean_batch_review`
  - `selected_handoff_clean_batch_review_status`
  - `handoff_require_clean_batch_review_count`
  - `handoff_clean_batch_review_count`
  - `handoff_unclean_batch_review_count`
  - `comparison_ready_handoff_require_clean_batch_review_count`
  - `comparison_ready_handoff_clean_batch_review_count`
  - `comparison_ready_handoff_unclean_batch_review_count`

这些字段不是重新计算出来的，而是从 promoted seed 的 baseline evidence 投影而来。这样 seed handoff 不会因为重复实现逻辑而和上游决策层产生解释偏差。

本版还新增 `_handoff_clean_batch_review_recommendations(summary)`：

- 如果 selected handoff 要求 clean batch review 但状态不是 `clean`，建议先修复 selected handoff clean batch-review status。
- 如果存在 `handoff_unclean_batch_review_count`，建议把 rejected dirty clean-required promoted inputs 保持在 seed handoff baseline 外。

这条 recommendation 是审查提示，不会改变 seed command 的默认执行语义。

### `src/minigpt/promoted_training_scale_seed_handoff.py`

主 builder 仍然负责：

1. 读取 promoted seed。
2. 解析 next plan command。
3. 根据 `execute` 决定只验证还是实际运行命令。
4. 加载 plan report 和 plan artifacts。
5. 组装 summary、requirement、recommendations。

v276 只在 `_summary()` 里新增一步：

```python
summary.update(build_seed_handoff_clean_batch_review_summary(baseline))
```

这样 JSON summary、CSV、Markdown、HTML、CLI stdout 都从同一份 summary 消费字段。它避免 artifact writer 自己去读 seed，也避免 CLI 和 HTML 各自写一套解析逻辑。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

artifact writer 是发布证据层。本版让三类输出都显式展示 clean batch-review evidence：

- CSV 增加字段列，适合 CI 或后续脚本机器读取。
- Markdown 增加 bullet，适合人工审查和讲解。
- HTML stats card 增加卡片，适合截图和浏览器验证。

关键点是：这些 artifact 只是把 summary 公开出来，不重新判断 selected baseline 是否可用。判断已经在 promoted comparison/decision/seed 层完成。

### `scripts/execute_promoted_training_scale_seed.py`

CLI 新增打印：

- `selected_handoff_require_clean_batch_review`
- `selected_handoff_clean_batch_review_status`
- `handoff_require_clean_batch_review_count`
- `handoff_clean_batch_review_count`
- `handoff_unclean_batch_review_count`
- `comparison_ready_handoff_require_clean_batch_review_count`
- `comparison_ready_handoff_clean_batch_review_count`
- `comparison_ready_handoff_unclean_batch_review_count`

这让命令输出本身成为轻量证据：不用打开 JSON，也能在终端日志和截图里确认 handoff 层接住了 clean batch-review context。

### `tests/test_promoted_training_scale_seed_handoff.py`

新增测试 `test_carries_seed_clean_batch_review_into_handoff_outputs_and_script()`。

测试 fixture 在 promoted seed 的 `baseline_seed` 中写入：

```json
"handoff_clean_batch_review": {
  "selected_handoff_require_clean_batch_review": true,
  "selected_handoff_clean_batch_review_status": "clean",
  "handoff_require_clean_batch_review_count": 3,
  "handoff_clean_batch_review_count": 2,
  "handoff_unclean_batch_review_count": 1,
  "comparison_ready_handoff_require_clean_batch_review_count": 2,
  "comparison_ready_handoff_clean_batch_review_count": 2,
  "comparison_ready_handoff_unclean_batch_review_count": 0
}
```

然后断言：

- builder summary 原样保留字段。
- CSV 包含字段名。
- Markdown/HTML 展示 clean batch-review 文案。
- CLI stdout 打印这些字段。
- JSON artifact 的 summary 保留 selected clean batch-review status。
- recommendation 提醒 dirty clean-required promoted inputs 只能作为被拒绝上下文保留，不应进入 seed handoff baseline。

这个测试保护的是跨层证据传递，不是模型训练质量。

## 输入输出格式

输入是 promoted seed JSON，核心输入段位于：

```text
baseline_seed.handoff_clean_batch_review
```

输出是 seed handoff report：

```text
promoted_training_scale_seed_handoff.json
promoted_training_scale_seed_handoff.csv
promoted_training_scale_seed_handoff.md
promoted_training_scale_seed_handoff.html
```

其中 JSON 的 `summary` 是后续模块最适合消费的机器接口。Markdown/HTML 是人工审查证据，CSV 是表格化导出，CLI stdout 是命令日志证据。

## 运行和验证

本版验证分四层：

- focused test：只跑 seed handoff 测试，确认新增字段和原有 suite alignment、clean-evidence requirement、batch review 测试共存。
- related chain test：跑 promoted comparison、promoted decision、promoted seed、promoted seed handoff，确认 v273-v276 的 clean batch-review 传播连续。
- full unittest：跑全量测试，确认没有破坏其他治理工具。
- source encoding：跑源码编码卫生检查，避免 BOM 或语法问题再次进入 CI。

运行截图和解释归档在 `c/276`。

## 链路角色

v276 的链路角色可以概括为：

```text
promoted comparison
  -> promoted decision
  -> promoted seed
  -> promoted seed handoff
```

前几层已经决定哪些 promoted inputs 可以进入 clean baseline；v276 让最后一层 handoff 在执行下一轮 plan 之前仍然能看见这份上下文。

## 一句话总结

v276 把 clean batch-review evidence 从 promoted seed 继续传到 promoted seed handoff，让下一轮训练规模计划在执行前也能保留“selected baseline 是否来自干净 promoted evidence”的审查证据。
