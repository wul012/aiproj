# v216 promoted seed handoff clean evidence CLI gate 代码讲解

## 本版目标

v216 的目标是让 v214/v215 的 clean-evidence readiness 可以被自动化显式执行。

前两版已经完成：

```text
v214: clean-evidence readiness 字段
v215: clean-evidence status-domain contract
```

v216 新增 `--require-clean-evidence`，让 CLI 在需要时检查 `seed_handoff_clean_evidence_ready`。这让 clean-evidence 从“报告里可读”推进到“脚本里可选执行”。

## 不做什么

本版不改变默认行为。没有传 `--require-clean-evidence` 时，seed handoff 仍按原来的 planned/execute/blocker 规则运行。

本版也不修改 `_handoff_allowed()`，不把 mismatch 或 missing 默认变成 blocker，不新增新的报告层。

## 前置路线

这版承接的是 promoted seed handoff 的证据链：

```text
suite alignment verdict
-> review recommendations
-> clean-evidence readiness
-> status-domain contract
-> opt-in CLI gate
```

它是把已有证据用于自动化，而不是继续增加报告。

## `scripts/execute_promoted_training_scale_seed.py`

### CLI 参数

新增参数：

```python
parser.add_argument(
    "--require-clean-evidence",
    action="store_true",
    help="Exit non-zero unless the seed handoff clean-evidence readiness is true.",
)
```

该参数默认关闭。

### 执行逻辑

CLI 仍然先构建 report，再写出 JSON/CSV/Markdown/HTML，然后打印 summary、command 和 outputs。

新增逻辑在输出写完之后运行：

```python
if args.require_clean_evidence:
    clean_evidence_ready = bool(summary.get("seed_handoff_clean_evidence_ready"))
    print(f"clean_evidence_required={'pass' if clean_evidence_ready else 'fail'}")
    if not clean_evidence_ready:
        raise SystemExit(1)
```

这样即使 gate 失败，调用者仍然可以查看输出文件分析原因。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增加两条测试：

1. `test_script_can_require_clean_evidence_after_consistent_execute`

   先执行 seed handoff，让 selected handoff、seed、plan suite path 达到 consistent，再加 `--require-clean-evidence`。测试断言 stdout 包含：

   ```text
   seed_handoff_clean_evidence_status=ready
   clean_evidence_required=pass
   ```

2. `test_script_rejects_pending_clean_evidence_when_required`

   不执行 plan，只验证 pending-plan handoff，并显式传入 `--require-clean-evidence`。测试断言 return code 非零，stdout 包含：

   ```text
   seed_handoff_clean_evidence_status=pending-plan
   clean_evidence_required=fail
   ```

   同时确认 JSON 输出仍然存在。

这两条测试保护了本版最重要的边界：默认不变，显式要求时才 gate。

## 运行证据

本版运行证据归档在 `c/216`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-promoted-training-scale-seed-handoff-clean-evidence-gate-smoke.png`
- `图片/03-promoted-seed-handoff-artifact-clean-evidence-gate-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、CLI gate pass/fail 都可见、gate 失败前 artifacts 已写出、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v216 让 promoted seed handoff 的 clean-evidence readiness 可以被 CI、smoke 或人工脚本显式要求。它不会替代人工审阅，但能在需要“只接受干净比较证据”的场景里提供一个明确出口。

## 一句话总结

v216 把 clean-evidence readiness 变成 opt-in CLI gate，让 promoted seed handoff 的证据不仅能展示，也能按需执行。
