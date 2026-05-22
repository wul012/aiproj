# v397 governance chain value review 代码讲解

## 本版目标和边界

v397 的目标是回应“aiproj 警惕治理链 N 次重复”的合理担忧：不继续新增下游 CI reason 字段，而是在已有 `maintenance_policy` 的 governance stabilization 里加入 value review，让项目能判断哪些治理链应该保留、监控、冻结新字段或先整合。

本版不新增第八条治理链，不改变训练、评测、promotion、seed handoff 的业务逻辑，也不删除现有报告。它只给现有七条链增加收口判断字段和机器可读汇总。

## 前置能力

v357-v363 已经建立 governance stabilization、proposal routing、keyword basis、ambiguous review 和 clean routing gate。v382-v396 又连续推进 CI regression reason counts。v397 基于这两条历史能力做一次收口：

```text
governance stabilization
        |
        +--> seven chain ceiling
        +--> proposal routing
        +--> v397 value / duplicate-risk / guardrail review
```

## 关键文件

### `src/minigpt/maintenance_policy.py`

默认七条治理链新增字段：

```text
value_status
duplicate_risk
recent_expansion
current_guardrail
guardrail_detail
```

字段含义：

- `value_status`：`core`、`supporting`、`watch`，说明这条链在项目里的价值位置。
- `duplicate_risk`：`low`、`medium`、`high`，说明继续投影字段或加报告时的重复风险。
- `recent_expansion`：描述近期扩展强度，例如 `stable`、`moderate`、`heavy`。
- `current_guardrail`：`keep-core`、`route-to-existing`、`freeze-new-fields`、`consolidate-first`。
- `guardrail_detail`：解释为什么这样收口。

默认配置里：

```text
training-promotion -> watch / high / heavy / freeze-new-fields
maturity-portfolio -> watch / high / heavy / freeze-new-fields
```

这正好对应 v382-v396 后“不要继续无边界传递 reason 字段”的判断。

`_governance_summary()` 新增汇总计数：

```text
core_value_count
supporting_value_count
watch_value_count
low_duplicate_risk_count
medium_duplicate_risk_count
high_duplicate_risk_count
heavy_recent_expansion_count
freeze_new_fields_count
```

`_governance_recommendations()` 会在有 freeze/high-risk 时提示冻结新字段，优先做整合、summary 或真实 benchmark 证据。

### `src/minigpt/maintenance_policy_governance_artifacts.py`

CSV、Markdown、HTML 都展示新增字段。Markdown 的 governance chains 表格现在不仅有 consumer/evidence/reason/rule，还能看到：

```text
Value status
Duplicate risk
Recent expansion
Guardrail
Guardrail detail
```

HTML stat cards 也展示 high duplicate-risk、heavy recent expansion 和 freeze-new-fields counts。

### `scripts/check_maintenance_batching.py`

CLI stdout 新增：

```text
governance_core_value_count
governance_supporting_value_count
governance_watch_value_count
governance_low_duplicate_risk_count
governance_medium_duplicate_risk_count
governance_high_duplicate_risk_count
governance_heavy_recent_expansion_count
governance_freeze_new_fields_count
```

这让命令行直接回答“当前有几条高重复风险链、几条应该冻结新字段”。

### `tests/test_maintenance_policy.py`

测试覆盖：

- 默认七链 value/risk/guardrail 计数；
- freeze-new-fields 高重叠链 recommendation；
- Markdown/HTML/CSV 输出字段；
- 脚本 stdout 暴露新增计数。

## 输入输出格式

输入仍是 governance chain list。默认输入不用额外文件，脚本会使用内置七条链。

输出仍是：

```text
maintenance_batching.json/csv/md/html
governance_stabilization.json/csv/md/html
```

新增字段写在 `governance_stabilization.*` 里，不影响原来的 maintenance batching 报告。

## 运行流程

```text
scripts/check_maintenance_batching.py
        |
        +--> build_maintenance_batching_report()
        +--> build_governance_stabilization_review()
                |
                +--> normalize seven chains
                +--> compute value/risk/guardrail counts
                +--> route optional proposals
                +--> write JSON / CSV / Markdown / HTML
                +--> print CLI counts
```

本版的核心结果是：

```text
governance_high_duplicate_risk_count=2
governance_freeze_new_fields_count=2
```

也就是 training-promotion 和 maturity-portfolio 两条链暂时不应继续加新字段投影。

## 测试覆盖

定向测试：

```text
python -m pytest tests/test_maintenance_policy.py -q
```

全量收口会继续运行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v397
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/397/图片
d/397/解释/说明.md
```

`d/397/解释/v397-governance-chain-value-review-evidence.html` 是给 Playwright MCP 截图的静态证据页；`runs/governance-value-review-v397` 是本轮临时验证输出，最终会按清理规则删除。

## 一句话总结

v397 把“治理链重复扩展风险”从口头判断变成可运行的维护策略：保留核心链，冻结高重叠链的新字段，下一步优先回到整合或真实 benchmark。
