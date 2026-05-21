# v339 CI tiny scorecard plan digests

## 本版目标和边界
v338 让 CI tiny scorecard wrapper 写出 invocation plan，记录固定预算、命令和 return code。v339 的目标是继续把这条证据链闭合：plan 不只说“运行了什么”，还要记录“运行后生成的 summary 与 summary-check sidecar 是哪几个文件、是否存在、大小是多少、sha256 是什么”。

本版不做的事：
- 不改变 tiny scorecard smoke 的训练、比较或 decision 逻辑
- 不改变 GitHub Actions 步骤
- 不新增新的评估分数
- 不把 digest 当作模型质量证据

## 前置路线

```text
v337 stable CI wrapper
  -> v338 wrapper invocation plan
  -> v339 summary/check artifact digests
```

## 关键文件

- `scripts/run_ci_tiny_scorecard_comparison_smoke.py`
  - 新增 summary/check 文件名常量
  - 新增 `build_summary_digest()`
  - 新增 `_file_digest()`
  - plan 中新增 `summary_digest`
  - 文本 plan 中镜像四个 sha256 字段
- `tests/test_ci_tiny_scorecard_smoke.py`
  - 新增 digest helper 测试
  - 真实 wrapper smoke 测试检查 digest 行存在
- `README.md`
  - 更新当前版本、v339 checkpoint 和 tag 说明
- `d/339/`
  - 保存本版运行截图和解释

## 核心数据结构

`summary_digest` 的结构：

```text
summary_digest
  artifacts
    summary_json
      path
      exists
      size_bytes
      sha256
    summary_text
      path
      exists
      size_bytes
      sha256
    summary_check_json
      path
      exists
      size_bytes
      sha256
    summary_check_text
      path
      exists
      size_bytes
      sha256
```

这四个 artifact 分别对应：

```text
tiny_scorecard_comparison_smoke_summary.json
tiny_scorecard_comparison_smoke_summary.txt
tiny_scorecard_comparison_smoke_check.json
tiny_scorecard_comparison_smoke_check.txt
```

如果文件不存在，digest 行会保留路径，`exists=false`，`size_bytes=0`，`sha256=""`。这样调用方能区分“没有记录”和“记录了但文件不存在”。

## 运行流程

v339 的 wrapper 顺序：

```text
build bottom smoke command
  -> run bottom smoke
  -> hash summary and check artifacts
  -> build invocation plan with returncode and summary_digest
  -> write plan JSON/text
  -> exit with bottom smoke returncode
```

digest 必须在底层 smoke 之后计算，因为 summary 与 summary-check sidecar 是底层 smoke 运行后才出现的。

## 文本输出

文本 plan 增加四个 shell-readable 字段：

```text
summary_json_sha256
summary_text_sha256
check_json_sha256
check_text_sha256
```

这些字段方便只看 CI 文本产物的人快速判断关键 artifact 是否稳定可追踪。

## 测试覆盖

新增和强化的测试：

1. `test_build_summary_digest_records_artifact_hashes`
   - 构造 summary/check 临时文件
   - 验证存在文件的 sha256 正确
   - 验证缺失文件也会产生明确的缺失 digest 行
2. `test_invocation_plan_records_wrapper_config_and_command`
   - 验证 plan 中包含 `summary_digest`
   - 验证文本 plan 能渲染 digest 字段
3. `test_wrapper_writes_invocation_plan_after_running_smoke`
   - 跑真实 wrapper smoke
   - 验证 plan 中 summary/check 四个 artifact digest 全部存在

## 链路角色

v339 让 CI tiny scorecard 证据链从：

```text
plan -> summary/check path
```

提升为：

```text
plan -> summary/check path + exists + size + sha256
```

它提升的是产物可追溯性，不是模型能力。

## 一句话总结
v339 给 CI tiny scorecard wrapper 的 plan 加上 summary/check artifact digest，让一次 tiny benchmark CI 运行能自证它生成并引用了哪些关键产物。
