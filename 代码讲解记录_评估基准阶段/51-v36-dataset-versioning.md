# 51-v36-dataset-versioning

## 本版目标、来源和边界

v36 的目标是给 prepared corpus 增加数据版本身份。v13/v15 已经能把多个 `.txt` 文件合并成 `corpus.txt`，并生成 `dataset_report.json`、`dataset_quality.json` 和 SVG 图表；但这些产物还缺少“这是哪个数据集、哪个版本、默认应该放到哪里、后续训练 run 如何引用”的版本层。

本版新增 `dataset_version.json` 和 `dataset_version.html`，并让 `scripts/prepare_dataset.py` 支持：

```powershell
--dataset-name sample-zh
--dataset-version v1
--dataset-description "Sample Chinese MiniGPT corpus"
```

如果传入 dataset name/version，默认输出目录会变成：

```text
datasets/<name>/<version>
```

本版不做三件事：

- 不引入外部数据仓库或远程数据下载。
- 不改变 corpus 合并和质量检查规则。
- 不声称数据来源已经满足生产合规，只记录版本、指纹和产物链路。

## 本版处在评估基准阶段的哪一环

当前评估基准链路是：

```text
source txt files
 -> prepared corpus
 -> dataset report
 -> dataset quality report
 -> dataset version manifest
 -> training run manifest / dashboard / playground / registry
 -> benchmark eval suite
```

v36 的重点是让后续模型对比能回答一个基础问题：每个 checkpoint 到底用了哪个 dataset version。

## 关键文件

```text
src/minigpt/data_prep.py
scripts/prepare_dataset.py
scripts/train.py
src/minigpt/manifest.py
src/minigpt/dashboard.py
src/minigpt/playground.py
src/minigpt/registry.py
tests/test_data_prep.py
tests/test_manifest.py
tests/test_dashboard.py
tests/test_playground.py
tests/test_registry.py
README.md
b/36/解释/说明.md
```

核心代码在 `data_prep.py`，训练和下游报告只负责携带这份版本证据。

## dataset_version.json 字段语义

新增 `build_dataset_version_manifest` 输出：

```json
{
  "schema_version": 1,
  "dataset": {
    "name": "sample-zh",
    "version": "v1",
    "id": "sample-zh@v1",
    "description": "..."
  },
  "created_at": "...",
  "preparation": {
    "recursive": true,
    "output_name": "corpus.txt",
    "source_roots": []
  },
  "stats": {
    "source_count": 2,
    "char_count": 1234,
    "line_count": 20,
    "unique_char_count": 120,
    "fingerprint": "...",
    "short_fingerprint": "..."
  },
  "quality": {
    "status": "pass",
    "warning_count": 0,
    "issue_count": 0
  },
  "outputs": {},
  "sources": []
}
```

这里的 `dataset.id` 是人读和脚本读都方便的版本标识；`stats.fingerprint` 继续来自 normalized prepared corpus，因此同样数据同样合并规则会得到稳定指纹。

## CLI 行为

旧命令继续可用：

```powershell
python scripts/prepare_dataset.py data --out-dir runs/dataset
```

新命令可以写入 named dataset directory：

```powershell
python scripts/prepare_dataset.py data --dataset-name sample-zh --dataset-version v1
```

CLI 会打印：

```text
dataset_id=sample-zh@v1
fingerprint=...
out_dir=datasets/sample-zh/v1
outputs={... "version_json": "...", "version_html": "..."}
```

这让终端截图和 CI 日志不用打开 JSON，也能看出本次数据版本身份。

## 下游 artifact 链路

本版把数据版本证据接入：

```text
scripts/train.py
src/minigpt/manifest.py
src/minigpt/dashboard.py
src/minigpt/playground.py
src/minigpt/registry.py
```

`scripts/train.py --prepared-data datasets/sample-zh/v1/corpus.txt` 会把同目录下的 `dataset_version.json/html` 复制到 run 目录。`build_run_manifest` 会把 dataset version summary 写入 `manifest["data"]["dataset_version"]`。Dashboard 会展示 dataset version id，Playground 和 Registry 也能发现对应 artifact。

## 输出产物

一次 versioned dataset preparation 现在包含：

```text
corpus.txt
dataset_report.json
dataset_report.svg
dataset_quality.json
dataset_quality.svg
dataset_version.json
dataset_version.html
```

`dataset_version.html` 是本版新增的浏览器报告，展示 dataset id、fingerprint、source count、quality、outputs 和 sources 表格。

## 测试覆盖链路

本版测试覆盖：

- `build_dataset_version_manifest` 写入 dataset id、short fingerprint、quality 和 outputs。
- `write_prepared_dataset` 默认生成 `dataset_version.json/html`。
- `build_run_manifest` 读取 `dataset_version.json` 并写入 `data.dataset_version`。
- Dashboard summary 读取 dataset version id。
- Playground links 发现 `dataset_version.html`。
- Registry artifact paths 包含 `dataset_version.json`。

这些断言保护的是数据版本证据链，而不是 HTML 样式本身。

## 归档和截图证据

本版运行证据放在：

```text
b/36/图片
b/36/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-dataset-version-smoke.png
03-dataset-version-structure-check.png
04-playwright-dataset-version.png
05-docs-check.png
```

其中 `02` 证明 CLI 能创建 named dataset version；`03` 证明 JSON/HTML 和下游 artifact 链路正确；`04` 证明新增 HTML 报告可以用真实 Chrome 打开；`05` 证明 README、b/36 归档和评估基准阶段讲解索引已经闭环。

## 一句话总结

v36 把 MiniGPT 的数据准备从“能合并 corpus”推进到“能给 corpus 一个稳定 dataset version 身份”，为后续模型横向对比打基础。
