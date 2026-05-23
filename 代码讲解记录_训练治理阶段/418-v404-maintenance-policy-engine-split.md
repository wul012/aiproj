# v404 Maintenance Policy Engine Split

## 版本目标

v404 的目标是拆分 `src/minigpt/maintenance_policy.py`。

它原本同时承担这些职责：

- 维护批处理策略。
- proposal 是否该合并/拆分的决策。
- 七条治理链的稳定化 review。
- governance proposal 路由。
- 维护压力 artifact facade。

这些职责堆在 648 行单文件里，已经超过项目约定的维护阈值。本版把它拆成 common、batching、governance 三层，同时保留原 `maintenance_policy.py` 作为 facade，避免脚本和测试断链。

本版不做的事：

- 不改变治理链默认数据。
- 不改变 batching、proposal routing、governance review 的输出 schema。
- 不新增新的治理链。

另外，本版验证时发现当前环境设置了 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY=http://127.0.0.1:7897`，导致 `tests/test_server.py` 的本地 `127.0.0.1` HTTP 测试被代理劫持并返回 502。这里顺手把测试 helper 改成无代理 opener，这属于本地测试可靠性修复，不改变 server 业务逻辑。

## 来源路线

这一版承接最近几版的维护收口节奏：

- v403 拆了 tiny scorecard comparison smoke。
- v404 继续处理当前最大生产文件 `maintenance_policy.py`。

它符合仓库规则：当单文件职责持续变宽并接近/超过 500-800 行时，做必要拆分。

## 关键文件

- `src/minigpt/maintenance_policy.py`
  - 现在是兼容 facade。
  - 继续导出 `build_maintenance_batching_report`、`build_governance_stabilization_review`、`build_maintenance_proposal_decision` 和 artifact helper。

- `src/minigpt/maintenance_policy_common.py`
  - 保存共享常量和归一化 helper。
  - 包括 `LOW_RISK_MAINTENANCE_CATEGORIES`、`HIGH_RISK_FLAGS`、category/modules/risk flags helper。

- `src/minigpt/maintenance_policy_batching.py`
  - 保存 maintenance batching report 和 proposal decision。
  - 负责判断 low-risk utils migration 是否应该合并成批次。

- `src/minigpt/maintenance_policy_governance.py`
  - 保存默认七条治理链。
  - 负责 governance stabilization review、proposal routing、keyword/exact matching 和 review recommendations。

- `tests/test_server.py`
  - 本地 HTTP helper 使用 `ProxyHandler({})` 构造无代理 opener。
  - 避免系统代理变量影响 `ThreadingHTTPServer(("127.0.0.1", 0), ...)` 这类本地测试。

## 核心数据流

batching 路径：

```text
history entries
  -> normalize release entry
  -> detect single-module utils runs
  -> build proposal decision
  -> build maintenance batching report
```

governance 路径：

```text
governance chains + proposed items
  -> normalize chains
  -> summarize value/risk/guardrail status
  -> route proposals by exact or keyword match
  -> produce stabilization recommendations
```

facade 路径：

```text
scripts/tests import minigpt.maintenance_policy
  -> facade re-exports split modules
  -> public API remains stable
```

## 测试覆盖

本版保留并运行维护策略相关测试：

- `tests/test_maintenance_policy.py`
  - 覆盖 batching policy、proposal decision、governance stabilization review、proposal routing 和 ambiguous keyword review。

- `tests/test_maintenance_policy_artifacts.py`
  - 覆盖 maintenance policy artifact facade 仍能写 JSON/CSV/Markdown/HTML。

- `tests/test_server.py`
  - 覆盖本地 HTTP health/generate/stream/pair 路径在有代理环境变量时仍直接访问测试服务器。

全量测试也会验证 facade 在其他链路中的兼容性。

## 证据边界

v404 的证据是维护性证据，不是模型能力证据。

它证明的是：

- 最大文件压力下降。
- public facade 没断。
- 维护策略、治理稳定化和 artifact 输出仍然可运行。

## 一句话总结

v404 把 maintenance policy 从一个 648 行混合引擎拆成了清晰的 common/batching/governance/facade 结构，让后续治理收口更容易维护。
