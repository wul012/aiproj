# 第一百零一版代码讲解：Experiment Card 接入 report_utils

## 本版目标

v101 的目标是把 `experiment_card.py` 接入 `report_utils`，让单次实验卡片也使用公共报告基础工具。

它解决的问题是：v100 已经让 model card 复用公共 JSON 写出、UTC 时间、HTML 转义和数据归一化工具，但 model card 的上游 experiment card 仍有自己的 `utc_now`、JSON 写出、HTML 转义和 `_dict`。v101 把这层也接进公共基础设施。

本版明确不做：

- 不改变 experiment card 字段结构。
- 不改变 run summary、data、training、evaluation、registry context 的生成策略。
- 不改变 artifact 收集和输出 artifact 标记逻辑。
- 不改变 recommendations 和 warnings 规则。
- 不改变 HTML/Markdown 布局。
- 不改 model card、project audit、release bundle 或 release gate。

## 路线来源

v101 延续 report-utils consolidation 路线。

相关治理链路是：

```text
run artifacts
 -> experiment card
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v100 把 model card 接入公共工具。
v101 继续把 model card 的上游 experiment card 接入公共工具。

这样从单 run 说明到模型说明、项目审计、发布总包，开始共享同一套基础写出和转义能力。

## 关键文件

- `src/minigpt/experiment_card.py`
  - 删除本地 `utc_now`。
  - 删除本地 `_dict`。
  - 删除本地 `_e`。
  - 删除 `datetime/timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`、`as_dict`。

- `tests/test_experiment_card.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 run + registry context、输出产物和 HTML escaping。

- `README.md`
  - 当前版本更新到 v101。
  - shared report infrastructure 更新到 experiment card migration。
  - 增加 v101 tag 和 `c/101` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `116-v101-experiment-card-report-utils.md` 索引。
  - 当前阶段基线更新到 v101。

- `c/101/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，experiment card 自己实现：

```python
utc_now()
write_experiment_card_json()
_dict()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    utc_now,
    write_json_payload,
)
```

`write_experiment_card_json()` 变成：

```python
def write_experiment_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)
```

这让 experiment card 的 JSON 输出行为和 model card、project audit、release bundle 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `_pick`
- `_pick_dict`
- `_nested_pick`
- `_as_int`
- `_as_optional_float`
- `_as_str`
- `_as_str_list`
- `_fmt`
- `_fmt_delta`
- `_fmt_int`
- `_rank_label`
- `_fmt_tags`
- `_fmt_mapping`
- `_fmt_any`
- `_md`
- `_artifact_href`
- `_tag_chips`

这些函数表达的是单 run 卡片自己的展示和数据提取语义。

例如：

- `_artifact_href` 根据 HTML 输出目录生成 artifact 链接。
- `_tag_chips` 把 run tags 渲染成 HTML chip。
- `_pick_dict` 和 `_nested_pick` 用来兼容 run manifest、registry run 和各类报告中的嵌套字段。
- `_fmt_int`、`_rank_label`、`_fmt_tags` 是 experiment card 的展示规则。

如果把这些迁到 `report_utils`，公共层会开始承载 experiment-card-specific 业务规则，边界反而变差。

## 数据结构和字段语义

experiment card 的主要输出仍然包括：

- `summary`
  - run 名称、状态、best val loss、loss rank、dataset quality、eval suite cases、git commit、parameter count。

- `notes`
  - note 和 tags，来自 run_notes 或 registry run。

- `data`
  - 数据来源、字符数、token 数、fingerprint、quality status 和 warning/issue 数。

- `training`
  - tokenizer、device、step、loss、batch/context 等训练配置和结果。

- `evaluation`
  - eval loss、perplexity、eval suite cases、unique chars 等评估上下文。

- `registry`
  - 是否匹配 registry run、rank、quality counts、tag counts 等多 run 上下文。

- `artifacts`
  - checkpoint、tokenizer、train config、dataset report、dashboard、playground、experiment card 自身输出等 artifact 状态。

- `recommendations`
  - 根据 missing artifacts、质量 warning、非最佳 run、缺 dashboard 等情况生成建议。

v101 没有改变这些字段，只改变公共写出和转义工具。

## 运行流程

experiment card 的流程仍然是：

```text
run directory
 -> train_config/history/dataset/eval/manifest/model_report/run_notes
 -> optional registry.json
 -> build_experiment_card()
 -> experiment_card.json
 -> experiment_card.md
 -> experiment_card.html
```

v101 改变的是：

- `generated_at` 使用公共 `utc_now`。
- JSON 写出使用公共 `write_json_payload`。
- HTML 转义使用公共 `html_escape`。
- dict 归一化使用公共 `as_dict`。

## 测试覆盖

本版使用 `tests.test_experiment_card` 做行为回归。

关键断言包括：

- run + registry context 能生成匹配的 run name、status、rank、dataset quality 和 tags。
- 输出函数仍然生成 JSON、Markdown、HTML 三类产物。
- HTML 标题、note 和 tag 文本仍然正确 escaping。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v101 的证据放在 `c/101`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-experiment-card-complete-smoke.png` 证明完整 run artifacts + registry context 能生成 ready summary。
- `03-experiment-card-missing-artifacts-smoke.png` 证明 sparse run 仍会保留 warnings/recommendations。
- `04-experiment-card-structure-check.png` 证明通用 helper 已迁移，experiment-card-specific helper 保留。
- `05-playwright-experiment-card-html.png` 证明 HTML 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v101 讲解文件互相对齐。

## 一句话总结

v101 把 experiment card 接入公共报告基础设施，让单 run 说明、模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留单次实验卡自己的 artifact 和展示语义。
