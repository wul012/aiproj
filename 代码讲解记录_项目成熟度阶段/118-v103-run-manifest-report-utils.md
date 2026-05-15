# 第一百零三版代码讲解：Run Manifest 接入 report_utils

## 本版目标

v103 的目标是把 `manifest.py` 接入 `report_utils`，让训练复现清单也使用公共报告基础工具。

它解决的问题是：v102 已经让 dataset card 复用公共 JSON 写出、UTC 时间、HTML 转义和 dict 归一化工具，但 run manifest 作为 dataset card 和 experiment card 的上游复现清单，仍然保留自己的 `utc_now`、JSON 写出和 HTML 转义。v103 把这层也接入公共基础设施。

本版明确不做：

- 不改变 run manifest 字段结构。
- 不改变 git、environment、data、model、training、results、artifacts 的生成策略。
- 不改变 artifact 规格列表。
- 不改变 SHA-256 计算规则和超大文件跳过 digest 的边界。
- 不改变 run manifest SVG 布局。
- 不改 dataset card、experiment card、model card、project audit、release bundle 或 release gate。

## 路线来源

v103 延续 report-utils consolidation 路线。

相关治理链路是：

```text
training run
 -> run manifest
 -> dataset card
 -> experiment card
 -> model card
 -> project audit
 -> release bundle
 -> release gate
```

v102 把 dataset card 接入公共工具。
v103 继续把 dataset card 和 experiment card 的上游 run manifest 接入公共工具。

这样训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包开始共享同一套基础写出和转义能力。

## 关键文件

- `src/minigpt/manifest.py`
  - 删除本地 `utc_now`。
  - 删除本地 `_e`。
  - 删除 `timezone` 和 `html` 直接导入。
  - 引入 `report_utils.utc_now`、`write_json_payload`、`html_escape`。
  - `write_run_manifest_json()` 改为调用公共 JSON 写出。

- `tests/test_manifest.py`
  - 本版不改测试文件。
  - 原有测试继续覆盖 SHA-256、artifact 收集、manifest 字段和 JSON/SVG 输出。

- `README.md`
  - 当前版本更新到 v103。
  - shared report infrastructure 更新到 run manifest migration。
  - 增加 v103 tag 和 `c/103` 截图说明。

- `代码讲解记录_项目成熟度阶段/README.md`
  - 增加 `118-v103-run-manifest-report-utils.md` 索引。
  - 当前阶段基线更新到 v103。

- `c/103/解释/说明.md`
  - 解释本版六张截图分别证明什么。

## 核心迁移点

迁移前，run manifest 自己实现：

```python
utc_now()
write_run_manifest_json()
_e()
```

迁移后，通用语义来自：

```python
from minigpt.report_utils import html_escape as _e, utc_now, write_json_payload
```

`write_run_manifest_json()` 变成：

```python
def write_run_manifest_json(manifest: dict[str, Any], path: str | Path) -> None:
    write_json_payload(manifest, path)
```

这让 run manifest 的 JSON 输出行为和 dataset card、experiment card、model card、project audit、release bundle 保持一致。

## 保留本地 helper 的原因

本版没有把下列 helper 迁走：

- `RUN_ARTIFACT_SPECS`
- `collect_run_artifacts`
- `sha256_file`
- `collect_git_metadata`
- `build_environment_metadata`
- `_git`
- `_read_json`
- `_dataset_report_summary`
- `_dataset_quality_summary`
- `_dataset_version_summary`
- `_duration_seconds`
- `_jsonable`
- `_pick`
- `_fmt_bytes`
- `_clip`

这些函数表达的是 run manifest 自己的复现清单语义。

例如：

- `RUN_ARTIFACT_SPECS` 定义训练运行应该追踪哪些产物。
- `sha256_file` 有 `max_digest_bytes` 边界，避免给超大 artifact 做昂贵 digest。
- `collect_git_metadata` 负责读取 commit、branch、tag 和 dirty 状态。
- `_duration_seconds` 把 started/finished 时间转成训练持续时间。
- `_fmt_bytes` 和 `_clip` 是 manifest SVG 的展示规则。

如果把这些迁到 `report_utils`，公共层会开始承载 run-manifest-specific 业务规则，边界反而变差。

## 数据结构和字段语义

run manifest 的主要输出仍然包括：

- `schema_version`
  - manifest schema 版本。

- `run_dir`
  - 当前训练运行目录。

- `created_at`、`started_at`、`finished_at`、`duration_seconds`
  - 记录训练开始、结束和持续时间。

- `command`
  - 记录训练命令，帮助复现实验。

- `git`
  - commit、short commit、branch、tag、dirty 状态。

- `environment`
  - Python、平台、可执行文件和额外环境信息。

- `data`
  - 原始数据来源、token count、train/val token count、dataset report summary、dataset quality summary、dataset version summary。

- `model`
  - 模型配置和参数量。

- `training`
  - 训练参数、tokenizer、device、start/end step。

- `results`
  - last loss 和 history summary。

- `artifacts`
  - checkpoint、tokenizer、train config、metrics、dataset reports、eval suite、model report、experiment card、dashboard、playground 等产物的存在性、大小和 digest。

v103 没有改变这些字段，只改变公共写出和转义工具。

## 运行流程

run manifest 的流程仍然是：

```text
training script / run directory
 -> dataset_report.json / dataset_quality.json / dataset_version.json
 -> build_run_manifest()
 -> collect git, environment, data, model, training, results, artifacts
 -> run_manifest.json
 -> run_manifest.svg
```

v103 改变的是：

- `utc_now` 使用公共 `report_utils.utc_now`。
- JSON 写出使用公共 `write_json_payload`。
- SVG 文本转义使用公共 `html_escape`。

## 测试覆盖

本版使用 `tests.test_manifest` 做行为回归。

关键断言包括：

- 小文件 SHA-256 仍然稳定。
- `collect_run_artifacts()` 仍能识别 checkpoint、metrics、experiment card 等产物。
- `build_run_manifest()` 仍然记录 duration、dataset report、dataset quality、dataset version、training args 和 history summary。
- `write_run_manifest_json()` 和 `write_run_manifest_svg()` 仍然写出 JSON/SVG 两类产物。

同时跑 `tests.test_report_utils`，确保公共工具行为稳定。

## 证据闭环

v103 的证据放在 `c/103`：

- `01-unit-tests.png` 证明聚焦测试、compileall 和全量 unittest 通过。
- `02-manifest-complete-smoke.png` 证明完整 run fixture 能生成 manifest JSON/SVG 和 artifact digest。
- `03-manifest-large-artifact-smoke.png` 证明超大 artifact 仍按 `max_digest_bytes` 跳过 SHA-256。
- `04-manifest-structure-check.png` 证明通用 helper 已迁移，run-manifest-specific helper 保留。
- `05-playwright-manifest-svg.png` 证明 SVG 能被真实 Chrome 打开。
- `06-docs-check.png` 证明 README、`c/README.md`、讲解索引和 v103 讲解文件互相对齐。

## 一句话总结

v103 把 run manifest 接入公共报告基础设施，让训练复现清单、数据说明、单 run 说明、模型说明、项目审计和发布总包这条治理链共享同一套基础工具，同时保留 manifest 自己的 artifact digest、git 探测和 SVG 展示语义。
