# 55-v40-checkpoint-comparison-shortcuts

## 本版目标、来源和边界

v40 的目标是把 v39 的 checkpoint selector 从“能选一个 checkpoint”推进到“能在 playground 里快速比较候选 checkpoint”。v37 已经有独立的 baseline model comparison，v38 有本地推理安全画像，v39 有 checkpoint 列表和选择路由；现在需要让本地服务和页面直接回答：

```text
当前可选 checkpoint 有几个是可用的？
哪个 checkpoint 缺 tokenizer 或模型元数据？
候选 checkpoint 相对 default 的参数量、文件大小、数据版本是否不同？
用户看到差异后，能不能马上切换到这个 checkpoint 或打开 model-info？
```

本版不做三件事：

- 不替代 v37 的完整 `compare_runs` 报告；这里只做 playground 内的轻量快捷比较。
- 不加载 PyTorch checkpoint 解析模型权重；比较信息来自文件状态和已有 JSON 元数据。
- 不评价生成文本好坏；生成质量仍交给 eval suite 和 generation quality 链路。

## 本版处在评估链路的哪一环

当前链路是：

```text
run directory / candidate checkpoint
 -> discover_checkpoint_options
 -> /api/checkpoint-compare
 -> checkpoint comparison rows
 -> playground comparison table
 -> Use button / model-info shortcut
 -> selected checkpoint generation
```

v40 的重点是把“候选 checkpoint 的差异”放到用户正在使用的 playground 里，而不是让用户在 README、命令行和多个 JSON 文件之间来回查。

## 关键文件

```text
src/minigpt/server.py
src/minigpt/playground.py
scripts/serve_playground.py
src/minigpt/__init__.py
tests/test_server.py
tests/test_playground.py
README.md
b/40/解释/说明.md
```

`server.py` 负责比较 payload 和 API；`playground.py` 负责浏览器表格、Use 动作和 model-info 链接；`serve_playground.py` 负责启动时打印 compare endpoint；测试和文档负责证明链路已经闭环。

## 新增比较 API

v40 新增：

```text
GET /api/checkpoint-compare
```

返回结构大致是：

```text
status
run_dir
default_checkpoint_id
checkpoint_count
summary
checkpoints[]
```

`summary` 记录整体数量：

```text
existing_count
missing_count
tokenizer_ready_count
ready_count
```

这让页面不用自己推断“有几个可用 checkpoint”，也让 smoke test 可以直接断言 ready/missing 状态。

## Checkpoint 比较行

每个 `checkpoints[]` 行来自 `CheckpointOption`，再补充比较字段：

```text
id
name
path
exists
is_default
tokenizer_path
tokenizer_exists
source
status
size_bytes
modified_utc
metadata_run_dir
model_info_endpoint
tokenizer
parameter_count
dataset_version
dataset_fingerprint
model_config
artifact_count
notes
size_delta_bytes
parameter_delta
same_tokenizer
same_dataset_version
same_dataset_fingerprint
same_model_config
```

字段语义：

- `status` 目前是 `ready` 或 `incomplete`，由 checkpoint 文件和 tokenizer 是否存在决定。
- `metadata_run_dir` 用于说明模型元数据从哪里读；如果候选 checkpoint 的父目录有 `run_manifest.json`、`train_config.json` 或 `dataset_version.json`，就优先读候选自己的目录。
- `model_info_endpoint` 是前端的快捷链接，形如 `/api/model-info?checkpoint=wide`。
- `size_delta_bytes` 和 `parameter_delta` 都以 default checkpoint 为 baseline。
- `same_*` 字段只在两边都有值时返回布尔值，否则返回 `null`，避免把“缺元数据”误判成“不同”。

## 元数据读取策略

v39 的 selector 只需要知道 checkpoint 文件在哪里。v40 的 compare 还要知道候选 checkpoint 对应的模型和数据版本，所以新增 `_metadata_run_dir`：

```text
如果 checkpoint 父目录存在 run_manifest.json / train_config.json / dataset_version.json
 -> 用 checkpoint 父目录作为 metadata run dir
否则
 -> 回退到 playground 的 run_dir
```

这样 `--checkpoint-candidate runs/wide/checkpoint.pt` 可以带上 `runs/wide/run_manifest.json` 里的参数量和 dataset version，而不是全部被误认为和当前 playground run 相同。

## Playground 前端

`playground.py` 新增 `Checkpoint Compare` 区块：

```text
button#refreshCheckpointCompareButton
output#checkpointCompareStatus
table#checkpointCompareTable
tbody#checkpointCompareBody
```

页面加载时会调用 `/api/checkpoint-compare`，把结果渲染成表格。表格字段包括：

```text
ID
Status
Size
Params
Dataset
Param delta
Size delta
Actions
```

Actions 里有两个动作：

- `Use`：把下拉框切到该 checkpoint，并刷新命令片段。
- `Model info`：打开 `/api/model-info?checkpoint=<id>`。

这就是“comparison shortcuts”的含义：比较不是单独的报告，而是直接服务于下一步选择、查看和生成。

## CLI 行为

`scripts/serve_playground.py` 启动时新增输出：

```text
checkpoint_compare=http://127.0.0.1:8000/api/checkpoint-compare
```

这样截图能证明服务端确实暴露了 compare endpoint。`--checkpoint-candidate` 沿用 v39 的参数，compare endpoint 会复用同一组候选 checkpoint。

## 测试覆盖链路

`tests/test_server.py` 新增或扩展断言：

- `build_checkpoint_compare_payload` 能读取 default 和 wide 的独立 `run_manifest.json`。
- wide 的 `parameter_delta` 相对 default 为正。
- wide 的 `dataset_version`、`model_config` 和 default 不同。
- `/api/health` 暴露 `checkpoint_compare_endpoint`。
- `/api/checkpoint-compare` 在真实 HTTP server 中返回候选 checkpoint。

`tests/test_playground.py` 新增断言：

- HTML 包含 `checkpointCompareTable`。
- 页面脚本会请求 `/api/checkpoint-compare`。
- 页面包含 `selectCheckpoint`，证明表格动作能反向驱动 selector。

这些测试保护的是“比较结果能从服务端进入页面，并反过来影响选择”的链路。

## 归档和截图证据

本版运行证据放在：

```text
b/40/图片
b/40/解释/说明.md
```

关键截图包括：

```text
01-unit-tests.png
02-checkpoint-compare-smoke.png
03-checkpoint-compare-structure-check.png
04-playwright-checkpoint-compare.png
05-docs-check.png
```

其中 `02` 证明 HTTP smoke 覆盖 compare endpoint、delta、model-info 和 generation；`03` 证明结构检查覆盖 ready count、参数差异、dataset 差异和前端动作；`04` 证明真实 Chrome 能打开包含 compare table 的 playground；`05` 证明 README、b/40 和讲解索引已经闭环。

## 一句话总结

v40 把 MiniGPT 的 playground 从“能选择 checkpoint”推进到“能在选择前快速比较 checkpoint，并把比较结果直接转化为 model-info 查看和生成选择动作”的阶段。
