# v457 promoted receipt summary-check failure smoke

## 本版目标和边界

v456 已经把 receipt contract summary-check 的失败归因拆成 `summary_field`、`contract_profile`、`sidecar` 三类 family。v457 不继续给报告加字段，而是补一层受控失败 smoke：自动复制一份合法 summary，再制造三类篡改，验证 v456 的 family summary 是否真的能把失败归到正确类别。

本版不改变 promoted seed handoff、不改变 receipt contract summary、不改变 summary-check 判定逻辑。它只新增一个验证入口，用来证明失败归因机制能在真实 JSON/HTML sidecar 产物上工作。

## 前置链路

本版承接：

- v451：summary-check 具备 summary field 和 sidecar digest rows。
- v455：summary-check 具备 contract profile consistency rows。
- v456：summary-check 具备 check family summary 和 failed target list。

v457 使用这些能力跑四个场景：

1. `baseline`
   - 不篡改，预期 summary-check 通过。
2. `tamper_summary_field`
   - 修改 `receipt_schema_version`，预期 `summary_field` family 失败。
3. `tamper_contract_profile`
   - 修改 `contract_check_type_summary`，预期 `contract_profile` 和 `summary_field` family 失败。
4. `tamper_sidecar`
   - 修改 HTML sidecar，预期 `sidecar` family 失败。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py`
  - 新增 failure smoke 主模块。
  - 负责复制 source summary、应用篡改、运行 summary-check、汇总场景矩阵。
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py`
  - 新增 CLI 入口。
  - 支持 `--out-dir`、`--force`、`--no-fail`。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py`
  - 覆盖模块 API、render 输出、文件写入和 CLI。

## 核心数据结构

`scenario_rows` 示例：

```json
{
  "scenario": "tamper_contract_profile",
  "tamper": "contract_check_type_summary",
  "status": "fail",
  "expected_status": "fail",
  "verification_status": "pass",
  "failed_families": ["contract_profile", "summary_field"],
  "expected_failed_families": ["contract_profile", "summary_field"],
  "failed_targets": ["summary.contract_check_type_summary"],
  "expected_failed_targets": ["summary.contract_check_type_summary"]
}
```

字段语义：

- `status`
  - 该场景实际 summary-check 状态。
- `expected_status`
  - 该场景预期的 summary-check 状态。
- `verification_status`
  - 状态、失败 family、失败 target 都符合预期才是 `pass`。
- `failed_families`
  - 从 v456 的 `check_family_summary` 读取出的失败类别。
- `failed_targets`
  - 从 v456 的 `failed_check_targets` 汇总出的失败目标。

## 运行流程

1. CLI 读取合法 contract summary 目录。
2. 为每个 scenario 复制一份 summary 到 `scenarios/<name>/summary`。
3. 按场景应用受控篡改。
4. 调用现有 summary-check，输出到 `scenarios/<name>/check`。
5. 从每个 check JSON 中读取 failed family 和 failed targets。
6. 比对 expected status、expected families、expected targets。
7. 写出顶层 failure smoke JSON/CSV/text/Markdown/HTML。

## 测试覆盖

Focused tests：

- 验证四个场景全部 `verification_status=pass`。
- 验证 `baseline` 通过且没有 failed families。
- 验证 `tamper_summary_field` 落入 `summary_field`。
- 验证 `tamper_contract_profile` 落入 `contract_profile` 和 `summary_field`。
- 验证 `tamper_sidecar` 落入 `sidecar`。
- 验证 CLI 能写出 failure smoke artifacts。

本版最终验证会覆盖：

- `python -m py_compile` 新增模块、脚本和测试。
- `python -m pytest tests/test_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.py -q -o cache_dir=runs/pytest-cache-v457-focused`
  - `2 passed`。
- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v457`
  - `787 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=358`，`clean_count=358`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/457` 保存本版证据：

- `解释/contract-summary/`：输入的合法 receipt contract summary。
- `解释/failure-smoke/`：failure smoke 顶层 JSON/CSV/text/Markdown/HTML，以及每个 scenario 的 summary/check 产物。
- `解释/failure-smoke-stdout.txt`：CLI 输出中可见 `status=pass`、`scenario_count=4`、`failed_verification_count=0`。
- `图片/01-failure-smoke-matrix.png`：Playwright MCP 截图，证明 HTML 矩阵展示四个场景。
- `解释/playwright_failure_smoke_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v457 把 v456 的失败归因能力从“报告里有字段”推进到“受控失败矩阵能证明归因正确”，让 summary-check 更适合进入 CI 和长期回归验证。
