# 第一百五十六版：server checkpoint payload 拆分

## 本版目标

v156 的目标是把本地推理服务里和 checkpoint 发现、health、model-info、checkpoint list、checkpoint comparison 相关的纯 payload 逻辑，从 `server_contracts.py` 拆到 `server_checkpoints.py`。

这一版解决的是 `server_contracts.py` 职责继续变宽的问题。v117 先把 server 契约从 HTTP handler 里抽出来，v125 把 PyTorch 生成器抽到 `server_generator.py`，v155 把 request-history 事件构造抽到 `server_logging.py`。到 v156，`server_contracts.py` 仍然承载了安全配置、请求解析、SSE/pair payload，以及 checkpoint metadata 处理。这里选择继续拆 checkpoint 边界，让 contracts 模块回到更纯粹的请求/响应契约层。

本版不做三件事：不改变 HTTP API 路径，不改变 checkpoint selector 行为，不改变 playground 端调用方式。它是 contract-preserving refactor，而不是功能重写。

## 前置路线

这版来自 v110 之后的 module pressure 路线，也承接 v117、v125、v155 的 server 拆分方向：

- v117：把 safety profile、请求解析、health/model-info/checkpoint/pair payload 从 `server.py` 抽到 `server_contracts.py`。
- v125：把 `MiniGPTGenerator` 抽到 `server_generator.py`，避免 HTTP handler 直接承担模型加载和 token 生成。
- v155：把 generation/pair-generation request-history 事件构造抽到 `server_logging.py`。
- v156：把 checkpoint discovery、metadata、model-info、comparison payload 抽到 `server_checkpoints.py`。

这个节奏符合之前的判断：不再继续堆 report-only 功能，而是用小步、定向的服务端边界整理降低维护成本。

## 关键文件

- `src/minigpt/server_checkpoints.py`  
  新增 checkpoint payload 模块，共 374 行。它负责 `CheckpointOption`、checkpoint discovery、health payload、model-info payload、checkpoint list payload、checkpoint comparison payload、metadata run dir 解析，以及内部 JSON/字段提取工具。

- `src/minigpt/server_contracts.py`  
  从 604 行降到 275 行。它继续保存 `InferenceSafetyProfile`、generation request/response dataclass、请求解析、SSE payload、pair payload。checkpoint 相关入口改为从 `server_checkpoints.py` 导入，并保留一个 `build_health_payload()` wrapper，用来继续提供默认 `InferenceSafetyProfile()`。

- `src/minigpt/server.py`  
  不需要重写路由。它通过原有 facade 继续暴露 checkpoint helpers，外部从 `minigpt.server` 导入旧名字时仍然可用。

- `tests/test_server_checkpoints.py`  
  新增 checkpoint 模块测试。它一边验证纯函数能读 checkpoint、tokenizer、run manifest 并生成 health/model-info/compare payload，一边验证 `server_contracts.py` 和 `server.py` 的旧导出仍然指向新模块。

## 核心数据结构

`CheckpointOption` 是 checkpoint selector 的核心记录：

```python
@dataclass(frozen=True)
class CheckpointOption:
    id: str
    name: str
    path: str
    exists: bool
    is_default: bool
    tokenizer_path: str | None
    tokenizer_exists: bool
    source: str
```

字段语义如下：

- `id`：给 API 和 playground 使用的稳定 checkpoint 标识，例如 `default`、`candidate`。
- `name`：更适合展示的名字，通常来自文件名或父目录名。
- `path`：真实 checkpoint 文件路径。
- `exists`：checkpoint 文件是否存在。
- `is_default`：是否是默认 checkpoint。
- `tokenizer_path` / `tokenizer_exists`：同一个 checkpoint 对应的 tokenizer 文件和存在性。
- `source`：发现来源，例如 `default`、`run-root`、`checkpoints`、`nested-run` 或 `candidate`。

这让 checkpoint 发现结果既能被 `/api/checkpoints` 展示，也能被 `/api/generate`、`/api/model-info` 和 pair comparison 复用。

## 核心函数

`discover_checkpoint_options()` 是入口之一。它从默认 checkpoint、显式 candidates、run root 下的 `*.pt`、`checkpoints/*.pt`、以及嵌套 run 的 `*/checkpoint.pt` 中收集候选，再用 `_path_key()` 去重，用 `_unique_checkpoint_id()` 避免 id 冲突。

`build_health_payload()` 负责 health endpoint 的 checkpoint 视角：

- 返回 run dir、默认 checkpoint、tokenizer/playground/sample lab 是否存在。
- 返回各个 endpoint 名称。
- 返回 checkpoint count 和 default checkpoint id。
- 接收 safety profile，但不直接依赖 `server_contracts.py`，避免循环导入。

`server_contracts.build_health_payload()` 仍然包一层默认安全配置：

```python
return _build_checkpoint_health_payload(
    run_dir,
    checkpoint_path,
    safety_profile=safety_profile or InferenceSafetyProfile(),
    request_log_path=request_log_path,
    checkpoint_candidates=checkpoint_candidates,
)
```

这保证旧入口没有传 safety profile 时，返回 payload 中仍然带默认安全边界。

`build_model_info_payload()` 聚合 `run_manifest.json`、`train_config.json`、`model_report/model_report.json`、`dataset_version.json`，输出 tokenizer、model config、parameter count、dataset version/fingerprint、git 信息和 artifact count。

`build_checkpoint_compare_payload()` 先发现 checkpoint，再对每个 checkpoint 生成 compare row，包括文件大小、修改时间、metadata run dir、model-info endpoint、参数量、数据版本、模型配置、artifact count 和 notes。随后 `_attach_checkpoint_deltas()` 以默认 checkpoint 为 baseline 追加 size、parameter、tokenizer、dataset、model config 的差异字段。

## 运行流程

典型调用链如下：

```text
server.py HTTP handler
  -> server_contracts facade
      -> server_checkpoints.discover_checkpoint_options()
      -> server_checkpoints.build_model_info_payload()
      -> server_checkpoints.build_checkpoint_compare_payload()
```

对外 API 仍然保持原样：

- `/api/health`
- `/api/model-info`
- `/api/checkpoints`
- `/api/checkpoint-compare`
- `/api/generate`
- `/api/generate-pair`

也就是说，这版只移动内部边界，不要求前端、脚本或用户改调用方式。

## 测试覆盖

新增 `tests/test_server_checkpoints.py` 覆盖两个层面：

- 纯函数链路：临时创建默认 checkpoint、candidate checkpoint、tokenizer、run manifest，断言 health 的 `default_checkpoint_id` 和 safety 字段、checkpoint count、compare row 里的 parameter count 和 dataset version、model-info 的 artifact count。
- 兼容导出：断言 `server_contracts.CheckpointOption`、`server_contracts.build_model_info_payload`、`server_contracts.build_checkpoint_compare_payload`、`server_contracts.discover_checkpoint_options`、`server_contracts.resolve_checkpoint_option`、`server_contracts.metadata_run_dir`，以及 `server.py` facade 中的对应导出，仍然和 `server_checkpoints.py` 中的对象是同一个。

这类 `assertIs` 不是形式测试。它保护的是旧 import path 不被破坏，也就是之前版本和用户脚本仍可继续运行。

## 维护压力结果

本版拆分前，维护扫描里最大模块是：

```text
largest_module=src\minigpt\server_contracts.py
```

拆分后：

```text
module_pressure_status=pass
module_warn_count=0
largest_module=src\minigpt\registry_render.py
```

这说明 `server_contracts.py` 的压力已经释放，下一轮若继续做代码质量优化，目标不应再盯着 server contracts，而应看新的最大模块或其他真实重复逻辑。

## 运行截图和证据

v156 的运行证据归档在 `c/156`：

- `01-server-checkpoint-tests.png`：证明 checkpoint 模块测试、server HTTP 测试、contract 测试、logging 测试、generator 测试一起通过。
- `02-server-checkpoint-smoke.png`：证明直接调用 `server_checkpoints.py` 能发现 checkpoint、读取 model-info，并生成 compare payload。
- `03-maintenance-smoke.png`：证明维护批处理和模块压力扫描仍为 pass，且 warn module 为 0。
- `04-source-encoding-smoke.png`：证明源码编码、BOM、语法和 Python 3.11 兼容性门禁通过。
- `05-full-unittest.png`：证明全量 unittest discovery 通过。
- `06-docs-check.png`：证明 README、`c/156`、代码讲解索引、运行说明、源码和测试关键词都已对齐。

这些截图是最终证据，不是后续模块直接消费的输入。后续模块如果要消费结果，应读取源码、测试和正式 JSON/Markdown artifact，而不是截图本身。

## 一句话总结

v156 把本地推理服务的 checkpoint 证据链从 server contracts 中拆成独立模块，让 checkpoint discovery、model-info 和 comparison payload 更容易测试、复用和继续维护，同时保持旧 API 与旧导出兼容。
