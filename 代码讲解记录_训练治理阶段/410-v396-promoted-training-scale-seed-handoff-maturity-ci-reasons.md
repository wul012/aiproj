# v396 promoted training scale seed handoff maturity CI reasons 代码讲解

## 本版目标和边界

v396 的目标是把 v394 已经进入 promoted seed 的 maturity CI regression reason counts 继续带到 final seed handoff。这样 `--require-clean-batch-review` 拦截 selected handoff 时，报告不仅知道有多少 CI regression，也知道原因分布是什么。

本版不改变 baseline 选择规则，不改变 next plan command，不改变 receipt schema，不新增训练任务，也不改变 clean batch-review gate 的通过条件。它只补齐 seed 到 handoff 的解释字段，让自动化失败可追踪。

## 前置能力

v394 已经把 promoted decision 的 CI regression reason counts 写入 seed。v395 又先拆出了 seed artifact HTML section，避免继续在接近 500 行的 artifact writer 上叠功能。v396 因此可以回到功能链路，把原因信息推进到 handoff。

```text
promoted decision
        |
        v
promoted seed summary
        |
        v
promoted seed handoff summary / requirement / report / CLI
```

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_review.py`

`build_seed_handoff_clean_batch_review_summary()` 现在会从 `baseline_seed["handoff_clean_batch_review"]` 读取并规范化以下字段：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts
selected_handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
```

这些字段都通过 `positive_int_mapping()` 清洗，空值、非 dict、零或负数计数不会进入输出。

`SeedHandoffCleanBatchReviewRequirement` 新增：

```text
selected_ci_regression_reason_counts
```

这个字段让 strict gate 失败时可以直接说明 selected handoff 的 CI regression 原因，而不是只给出 `selected_ci_regression_count`。

推荐语也改为包含 `format_mapping()` 输出。例如 rejected promoted decision inputs 有 CI regression 时，recommendation 会带上 observed reasons。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 输出新增 reason-count 字段，覆盖 selected、aggregate、comparison-ready 和 requirement 层：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts
selected_handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
clean_batch_review_requirement_selected_ci_regression_reason_counts
```

CSV 使用 `format_mapping()` 写成人类和脚本都容易读的 `reason:count` 形式。

### `src/minigpt/promoted_training_scale_seed_handoff_sections.py`

Markdown 和 HTML stat cards 展示同一批 reason-count 字段。Markdown 是线性证据，HTML 是运行截图入口，二者都不是新的事实源，而是从 handoff report summary 渲染出来的只读视图。

### `scripts/execute_promoted_training_scale_seed.py`

CLI stdout 新增 selected、aggregate、comparison-ready 和 requirement reason-count 行。这样 CI 或 shell 日志只看 stdout，也能知道 strict clean-batch gate 为什么失败。

## 输入输出格式

输入仍来自 promoted seed 的 `baseline_seed.handoff_clean_batch_review`：

```json
{
  "selected_handoff_batch_maturity_ci_regression_count": 1,
  "selected_handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1
  }
}
```

handoff summary 会保留清洗后的 dict：

```json
{
  "selected_handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1
  }
}
```

CSV、Markdown、HTML 会把它格式化为：

```text
missing-ci-step:1
```

CLI stdout 会保留 JSON 风格，方便脚本读取：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts={"missing-ci-step": 1}
```

## 运行流程

```text
build_promoted_training_scale_seed_handoff()
        |
        +--> load promoted seed baseline
        +--> build_seed_handoff_clean_batch_review_summary()
        |       |
        |       +--> copy CI counts
        |       +--> normalize reason-count mappings
        |
        +--> build_seed_handoff_clean_batch_review_requirement()
        |       |
        |       +--> include selected reason counts
        |
        +--> write JSON / CSV / Markdown / HTML
        +--> print CLI diagnostics
```

clean-batch gate 仍然只依据 selected status 和 selected CI regression count 判断 pass/fail。reason counts 是解释字段，不改变门禁逻辑。

## 测试覆盖

定向测试：

```text
python -m pytest tests/test_promoted_training_scale_seed_handoff.py -q
```

覆盖点：

- handoff summary 保留 aggregate reason counts；
- selected strict gate failure 保留 selected reason counts；
- `clean_batch_review_requirement` 保留 selected reason counts；
- CSV 写出 reason-count 字段；
- Markdown/HTML 展示 reason-count 文本；
- CLI stdout 输出 JSON 风格的 reason-count 行；
- 原有 clean-batch strict gate 的 fail 行为不变。

全量收口还会运行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v396
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/396/图片
d/396/解释/说明.md
```

`d/396/解释/v396-promoted-training-scale-seed-handoff-maturity-ci-reasons-evidence.html` 是给 Playwright MCP 截图用的静态证据页，不是机器消费的最终报告。

## 一句话总结

v396 把 promoted seed 的 CI regression 原因解释带到最终 seed handoff，让 clean-batch automation stop 从“知道失败数量”升级为“知道失败原因”。
