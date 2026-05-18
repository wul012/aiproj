# v219 promoted seed handoff clean evidence requirement contract 代码讲解

## 本版目标

v219 的目标是把 clean-evidence requirement 从 CLI 私有逻辑提升为 seed handoff 的库级契约。

v216 到 v218 已经完成三步：

```text
v216 opt-in CLI gate
v217 structured gate diagnostics
v218 persisted gate artifacts
```

但 v218 的 `not-required/pass/fail` 计算仍在 `scripts/execute_promoted_training_scale_seed.py` 内部。v219 把这段判断移动到 `src/minigpt/promoted_training_scale_seed_handoff.py`，让库调用方、CLI 和 artifact writer 使用同一个对象。

本版也融合一个轻量维护项：删除只转调 `report_utils.utc_now()` 的本地 `_utc_now()` wrapper，避免时间戳 helper 再次分散。

## 不做什么

本版不改变默认 seed handoff 行为。

不改变 `--execute`。

不改变 `--require-clean-evidence` 的退出码策略。

不新增独立报告，也不改变 suite alignment 或 clean-evidence readiness 的判断标准。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff.py`

本版新增 requirement status 的类型和公开状态域：

```python
SeedHandoffCleanEvidenceRequirementStatus = Literal["not-required", "pass", "fail"]

SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES = (
    "not-required",
    "pass",
    "fail",
)
```

这里和 v215 的 readiness status domain 分开：

```text
readiness: ready / pending-plan / review / incomplete
requirement: not-required / pass / fail
```

前者说明 clean evidence 是否真的准备好；后者说明本次是否要求它，以及要求后是否通过。

### `build_seed_handoff_clean_evidence_requirement()`

新增 helper：

```python
def build_seed_handoff_clean_evidence_requirement(
    summary: dict[str, Any],
    *,
    required: bool = False,
) -> SeedHandoffCleanEvidenceRequirement:
```

输入是 seed handoff summary，输出是稳定对象：

```text
required
status
ready
readiness_status
detail
status_domain
```

状态转换规则很小：

```text
required=False -> not-required
required=True and ready=True -> pass
required=True and ready=False -> fail
```

这个 helper 不重新计算 suite alignment，只消费已有 summary。这一点很重要，因为 v212-v214 已经把 alignment verdict 和 clean-evidence readiness 做成上游证据，v219 只负责 requirement gate 的最后一层解释。

### `build_promoted_training_scale_seed_handoff()`

builder 新增参数：

```python
require_clean_evidence: bool = False
```

构建完 summary 后，builder 直接写入：

```python
clean_evidence_requirement = build_seed_handoff_clean_evidence_requirement(
    summary,
    required=require_clean_evidence,
)
```

返回 report 时包含：

```text
clean_evidence_requirement
```

这意味着不用经过 CLI，Python 调用方也能得到和 CLI artifact 完全一致的 gate 决策。

### `scripts/execute_promoted_training_scale_seed.py`

CLI 不再持有 `_clean_evidence_requirement()` 私有函数。

它只把参数传给 builder：

```python
require_clean_evidence=args.require_clean_evidence
```

然后读取：

```python
clean_evidence_requirement = report["clean_evidence_requirement"]
```

这让 CLI 从“规则拥有者”退回到“规则消费者”。后续如果要接 CI 或其他自动化，不需要复制脚本内部逻辑。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

artifact 输出补充 requirement status domain：

```text
clean_evidence_requirement_status_domain
Clean evidence requirement status domain
Clean evidence gate domain
```

这些字段的作用不是改变判断，而是让下游读取 artifact 时知道合法状态空间。

## `utc_now` 收敛

本版删除了几个只做转调的本地 wrapper：

```text
benchmark_scorecard_comparison._utc_now()
comparison._utc_now()
data_prep._utc_now()
request_history._utc_now()
training_portfolio_comparison._utc_now()
```

对应调用点改为直接使用：

```python
utc_now()
```

来自：

```python
from minigpt.report_utils import utc_now
```

这属于轻量、定向的质量优化。`manifest.py` 的 `datetime.fromisoformat()`、`server_checkpoints.py` 的文件修改时间格式化不属于重复生成时间 helper，所以本版没有动。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 增加和扩展了这些断言：

1. `SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES` 是公开契约，值固定为 `not-required/pass/fail`。
2. `build_seed_handoff_clean_evidence_requirement()` 正确把 pending summary 映射为 `not-required` 或 `fail`，把 ready summary 映射为 `pass`。
3. builder 在 `require_clean_evidence=True` 时直接生成 `clean_evidence_requirement`，planned 场景为 `fail`，execute 后 consistent 场景为 `pass`。
4. CLI 继续保持 stdout gate 诊断和退出码行为。
5. JSON/CSV/Markdown/HTML 都包含 requirement status domain。

这些断言保护的是“CLI 和库调用方共享同一份 requirement contract”。

## 运行证据

本版运行证据归档在 `c/219`：

- `图片/01-promoted-training-scale-seed-handoff-tests.png`
- `图片/02-utc-now-convergence-check.png`
- `图片/03-promoted-seed-handoff-requirement-contract-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、重复 `_utc_now` wrapper 清零、库级和 CLI artifact 契约一致、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v219 让 seed handoff clean-evidence gate 更适合后续自动化消费。

过去的调用方式是：

```text
CLI stdout / CLI artifact
```

现在的调用方式可以是：

```text
library report -> clean_evidence_requirement
CLI stdout -> clean_evidence_required=...
artifact -> clean_evidence_requirement
```

三条路径共享同一个 requirement 对象。

## 一句话总结

v219 把 clean-evidence requirement 从 CLI 内部判断升级为库、CLI、artifact 共享的稳定契约，并顺手收敛了重复时间戳 wrapper。
