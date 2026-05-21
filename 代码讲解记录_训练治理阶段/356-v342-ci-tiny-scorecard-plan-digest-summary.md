# v342 CI tiny scorecard plan digest summary

## 本版目标和边界

v341 已经把 `check_ci_tiny_scorecard_plan.py` 接进 GitHub Actions，并让 CI workflow hygiene 把它放到 tiny smoke 之后、coverage 之前。v342 的目标是把这条 gate 的结果提升成更容易被下游消费的 summary 字段，并把它透传进 project audit context。

本版不做的事：

- 不改变 tiny smoke、wrapper 或 checker 的执行顺序
- 不改变训练、生成、评分或 coverage 的逻辑
- 不增加新的证据层
- 不把 gate ready 写成模型质量证明

## 前置路线

```text
v340 reusable plan digest checker
  -> v341 CI-enforced plan digest gate
  -> v342 summary-level gate propagation
```

## 关键文件

- `src/minigpt/ci_workflow_hygiene.py`
  - 新增 `tiny_scorecard_plan_digest_gate_present`
  - 新增 `tiny_scorecard_plan_digest_gate_order_ready`
  - 新增 `tiny_scorecard_plan_digest_gate_ready`
  - 让 summary 可以直接表达 gate 是否存在、是否顺序正确、是否真正 ready
- `src/minigpt/ci_workflow_hygiene_artifacts.py`
  - 在 Markdown / HTML / 表格统计中渲染 gate ready 字段
  - 让人读报告时不必先扫 check rows
- `src/minigpt/project_audit_contexts.py`
  - 把 CI workflow hygiene 的 gate ready 字段带入 audit check evidence
  - 把 gate ready 写入 audit check detail
- `src/minigpt/project_audit.py`
  - 把 gate ready 传进 project audit summary，供更上层的 release / maturity 链路消费
- `tests/test_ci_workflow.py`
  - 覆盖 current workflow、旧 workflow、坏顺序、渲染输出
- `tests/test_project_audit.py`
  - 覆盖 audit summary 和 context 对 gate ready 字段的透传
- `README.md`
  - 更新当前版本、成熟度说明、v342 checkpoint 和 tag
- `d/342/`
  - 保存本版截图和解释

## 核心字段

`ci_workflow_hygiene.summary` 新增三个布尔字段：

```text
tiny_scorecard_plan_digest_gate_present
tiny_scorecard_plan_digest_gate_order_ready
tiny_scorecard_plan_digest_gate_ready
```

含义分别是：

- `present`：workflow 里是否真的出现了 plan digest check 命令
- `order_ready`：这个命令是否位于 tiny smoke 之后、coverage 之前
- `ready`：前两者同时成立

这三个字段是摘要级信号，不是替代明细 checks 的新证据层。

## project audit 角色

project audit 以前已经消费 CI workflow hygiene，但主要看的是总 status、failed checks、order violations。v342 让它还能直接看到：

```text
tiny_scorecard_plan_digest_gate_ready
```

这对 release / maturity 读取更友好，因为下游不必再拆开 workflow hygiene 明细去找 tiny plan digest gate。

## 测试覆盖

测试覆盖四件事：

1. 当前真实 workflow 的 gate ready 为 `True`
2. coverage 提前时，gate ready 变为 `False`
3. plan checker 放在 tiny smoke 前时，gate ready 也变为 `False`
4. project audit 能把这个 ready 状态带进 summary 和 evidence

## 链路角色

v342 做的是字段收口：

```text
workflow YAML
  -> ci_workflow_hygiene summary
  -> project_audit context
  -> release/maturity consumers
```

这让 tiny scorecard plan digest gate 从“明细条目”变成“可直接消费的治理信号”。

## 一句话总结

v342 让 CI tiny scorecard plan digest gate 不只是能被检查，还能被下游治理摘要直接读取和复用。
