# v679 required-term pair surface failure diagnostic

## 本版目标和边界

v679 的目标是对 v678 的 closeout 结论继续下钻：既然 internal forced-choice 已经多 seed 稳定，但 generation pair-full 只有 2/3，那么需要知道失败具体发生在哪里。

本版只做只读诊断，不训练模型、不改 corpus、不设计新 prompt policy。它的产物是后续 generation-surface replay 的输入依据。

## 前置链路

v676 给出 generation seed stability：

- seed `1535`: pair-full
- seed `2535`: no pair-full
- seed `3535`: pair-full

v677 给出 forced-choice internal scoring：

- seed `1535`: internal pair match
- seed `2535`: internal pair match
- seed `3535`: internal pair match

v678 将这两层收口为：内部偏好稳定，但生成表面不稳定。v679 继续定位具体失败 term。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_surface_failure_diagnostic.py`
  - 读取 seed stability 与 forced-choice 报告。
  - 将 seed rows、embedded seed refresh reports、forced-choice source summaries 按 seed 对齐。
  - 计算 `surface_failure_terms`、`dominant_failure_term` 和 `classification`。

- `src/minigpt/model_capability_required_term_pair_surface_failure_diagnostic_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 展示失败 seed、missed terms 和 preview。

- `scripts/run_model_capability_required_term_pair_surface_failure_diagnostic.py`
  - CLI 入口，支持目录或 JSON 输入、`--require-pass`、`--force`。

- `tests/test_model_capability_required_term_pair_surface_failure_diagnostic.py`
  - 覆盖单 term 失败、无失败、坏输入、输出格式。

## 输入输出

输入：

- `e/676/解释/model-capability-required-term-pair-dual-boundary-seed-stability/`
- `e/677/解释/model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice/`

运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_surface_failure_diagnostic.py e\676\解释\model-capability-required-term-pair-dual-boundary-seed-stability e\677\解释\model-capability-required-term-pair-dual-boundary-multi-seed-forced-choice --out-dir e\679\解释\model-capability-required-term-pair-surface-failure-diagnostic --require-pass --force
```

输出：

- `model_capability_required_term_pair_surface_failure_diagnostic.json`
- `model_capability_required_term_pair_surface_failure_diagnostic.csv`
- `model_capability_required_term_pair_surface_failure_diagnostic.txt`
- `model_capability_required_term_pair_surface_failure_diagnostic.md`
- `model_capability_required_term_pair_surface_failure_diagnostic.html`

## 核心字段语义

- `generation_pair_full`: 该 seed 自由生成是否同时命中 fixed/loss。
- `generation_hit_terms`: 自由生成命中的 term。
- `generation_missed_terms`: 自由生成漏掉的 term。
- `internal_pair_full`: forced-choice 内部评分是否同时通过 fixed/loss。
- `surface_failure_terms`: 内部已通过但自由生成漏掉的 term。
- `dominant_failure_term`: 本 seed 最主要的 surface failure term。
- `best_generation_preview`: 漏掉 term 对应的 continuation preview，用于判断是空白、片段还是错误词。
- `classification`: seed 分类，例如 `aligned_pair_full` 或 `internal_stable_surface_failure`。

## 本版结果

真实报告显示：

- `surface_failure_seeds=[2535]`
- `surface_failure_terms=['loss']`
- `decision=required_term_pair_single_term_surface_failure_isolated`

这说明问题已经从“大方向不明”缩小为 seed 2535 的 `loss` 生成表面失败。

## 测试与证据

验证命令：

```powershell
python -m py_compile src\minigpt\model_capability_required_term_pair_surface_failure_diagnostic.py src\minigpt\model_capability_required_term_pair_surface_failure_diagnostic_artifacts.py scripts\run_model_capability_required_term_pair_surface_failure_diagnostic.py tests\test_model_capability_required_term_pair_surface_failure_diagnostic.py
python -m pytest tests\test_model_capability_required_term_pair_surface_failure_diagnostic.py -q -o cache_dir=runs\pytest-cache-v679
```

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/679/解释/model-capability-required-term-pair-surface-failure-diagnostic/`
- 截图: `e/679/图片/v679-surface-failure-diagnostic.png`
- 解释: `e/679/解释/说明.md`

一句话总结：v679 将下一阶段目标明确为 generation-surface policy replay，而不是继续修内部偏好。
