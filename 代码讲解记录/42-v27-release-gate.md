# v27 Release Gate 代码讲解

v27 在 v26 的 `release_bundle.json` 之后增加了一层自动化门禁。v26 负责“把证据放在一起”，v27 负责“根据证据判断能不能放行”。

核心文件：

```text
src/minigpt/release_gate.py
scripts/check_release_gate.py
tests/test_release_gate.py
```

## 角色

`release_gate.py` 读取 release bundle，并生成新的 `gate_report.json`、`gate_report.md`、`gate_report.html`。

它不重新训练模型，也不重新计算指标，而是把已有证据转成一个更适合脚本和 CI 使用的结论：

```text
release_bundle.json
 -> build_release_gate
 -> checks
 -> gate_status: pass / warn / fail
 -> decision: approved / needs-review / blocked
 -> gate_report.json/md/html
```

## 核心流程

入口函数是 `build_release_gate`：

```python
def build_release_gate(
    bundle_path: str | Path,
    *,
    minimum_audit_score: float = 90.0,
    minimum_ready_runs: int = 1,
    title: str = "MiniGPT release gate",
    generated_at: str | None = None,
) -> dict[str, Any]:
```

它做四件事：

1. 读取 `release_bundle.json`。
2. 根据门禁策略构造一组 checks。
3. 汇总 checks，得到 `gate_status` 和 `decision`。
4. 返回一个完整 gate report 字典。

默认策略保存在输出的 `policy` 字段里：

```text
required_release_status = release-ready
required_audit_status = pass
minimum_audit_score = 90
minimum_ready_runs = 1
require_all_evidence_artifacts = True
```

这意味着：不是“看起来差不多就行”，而是要求 release bundle 的核心证据完整。

## Checks 如何判断

`_build_checks` 是 v27 的核心。

它从 release bundle 的 `summary`、`top_runs`、`audit_checks`、`warnings` 中取值，然后生成固定检查项：

```text
bundle_schema
release_status
audit_status
audit_score
ready_runs
best_run
evidence_artifacts
top_runs
audit_checks
bundle_warnings
```

每个 check 都是统一结构：

```json
{
  "id": "audit_score",
  "title": "Audit score meets threshold",
  "status": "pass",
  "detail": "audit_score=100%; minimum=90%."
}
```

这种结构的好处是：

- JSON 适合程序读取。
- Markdown 适合 README 或报告粘贴。
- HTML 适合浏览器查看。
- CLI 可以根据 `status` 直接决定退出码。

## Gate Status 与 Decision

`_build_summary` 会统计 checks：

```text
pass_count
warn_count
fail_count
```

然后映射成最终状态：

```text
有 fail -> gate_status = fail, decision = blocked
无 fail 但有 warn -> gate_status = warn, decision = needs-review
全 pass -> gate_status = pass, decision = approved
```

这里故意把 `gate_status` 和 `decision` 分开：

- `gate_status` 更适合机器判断。
- `decision` 更适合人读报告。

## 退出码

`exit_code_for_gate` 让这个功能可以用于自动化：

```python
def exit_code_for_gate(gate: dict[str, Any], *, fail_on_warn: bool = False) -> int:
```

默认规则：

```text
fail -> 1
warn -> 0
pass -> 0
```

如果命令加 `--fail-on-warn`：

```text
warn -> 1
```

也就是说，本地展示可以允许 warn，CI 发布可以把 warn 也视为失败。

## CLI 脚本

`scripts/check_release_gate.py` 是命令行入口：

```powershell
python scripts/check_release_gate.py --bundle runs/release-bundle/release_bundle.json --out-dir runs/release-gate
```

它会输出：

```text
gate_status=pass
decision=approved
checks=10 pass/0 warn/0 fail
outputs={"json": "...", "markdown": "...", "html": "..."}
```

如果门禁失败，脚本会以 `SystemExit(1)` 退出，这样 GitHub Actions、批处理脚本、PowerShell 自动化都能识别失败。

## 测试覆盖

`tests/test_release_gate.py` 主要覆盖五类场景：

- 完整 release bundle 可以通过门禁。
- bundle 有 warning 时进入 `needs-review`。
- release blocked、audit failed、artifact 缺失时门禁失败。
- JSON/Markdown/HTML 输出文件存在。
- HTML 会转义 `<script>` 这类危险文本。

## 一句话总结

v27 把 MiniGPT 的发布流程从“人工看报告”推进到“脚本可判断能否发布”：release bundle 是证据，release gate 是放行决策。
