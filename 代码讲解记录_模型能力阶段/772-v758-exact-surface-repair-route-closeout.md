# v758 exact-surface repair route closeout 代码讲解

## 本版目标和边界

v758 的目标是把 v757 的 comparison 结论变成一份可执行的 route closeout。v757 已经证明 v753-v756 的 near-exact repair route 没有带来独立 replay 改善，v758 不再重复对比，也不继续训练，而是把“不要继续这条路”的工程边界固化为 JSON/Markdown/HTML 证据。

本版边界很重要：它不宣称模型能力提升，不新增训练数据，不推广 v755 checkpoint。它只回答一个问题：这条 exact-surface repair route 是否应该继续投入？答案是关闭。

## 前置路线

- v753：把 v752 exact-surface repair plan 落成四行 contract patch。
- v754：将 contract patch 物化为 7680 行训练 corpus。
- v755：训练真实 tiny checkpoint，训练脚本内观察到 pair-full。
- v756：独立 pair-probe replay 后只得到 partial 证据。
- v757：对比 v750 与 v756，确认 exact/spaced/arrow surface 的 delta 都是 0。
- v758：把 ineffective comparison 转成路线关闭和下一步候选路线。

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.py`
  - closeout 核心逻辑。
  - 输入 v757 effectiveness comparison JSON。
  - 校验 comparison 必须是 `pass` 且 decision 必须是 `pair_readiness_exact_surface_repair_ineffective_stop_route`。
  - 生成 `do_not_continue`、`candidate_routes`、`summary` 和 `interpretation`。

- `src/minigpt/model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
  - HTML 页面展示 summary cards、do-not-continue 列表、候选路线和 checks。

- `scripts/run_model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.py`
  - CLI 入口。
  - 支持输入 v757 JSON 文件或输出目录。
  - `--require-pass` 下 closeout check 失败会返回非 0。

- `tests/test_model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.py`
  - 覆盖 ready closeout、非 ineffective route 失败、目录 locator 和多格式 artifact 输出。

## 输入输出结构

输入来自 v757：

```text
status=pass
decision=pair_readiness_exact_surface_repair_ineffective_stop_route
repair_ineffective=True
exact_default_hit_delta=0
exact_pair_full_delta=0
```

v758 输出：

```text
status=pass
decision=pair_readiness_exact_surface_repair_route_closed
closeout_ready=True
closed_route=near_exact_surface_bridge_rows
recommended_next_route=objective_or_decoding_alternative_plan
candidate_route_count=3
```

## closeout 字段解释

`closed_route` 是被关闭的路线名。这里明确是 `near_exact_surface_bridge_rows`，也就是继续追加近似 exact prompt 的 bridge rows。

`do_not_continue` 是硬边界：

- 不继续追加同类 near-exact pipe/equals rows。
- 不推广 v755 checkpoint。
- 不把训练脚本内部 pair-full 当成独立 replay-ready 证据。

`candidate_routes` 是下一步候选方向：

| route | 含义 | 风险 |
| --- | --- | --- |
| objective_level_contrast | 改训练目标，让模型学习响应目标而不是表面模式 | 仍可能过拟合 tiny prompt |
| decode_side_constraint_probe | 用解码侧约束确认 exact prompt 是否受 first-token/separator 影响 | 可能掩盖模型本身弱点 |
| fresh_seed_stability | 先确认 partial pattern 是否只是 seed 偶然性 | 训练成本更高 |

## 测试和验证

Focused tests：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.py -q -o cache_dir=runs\pytest-cache-v758-focused
```

结果为 4 个测试通过。

真实运行命令：

```powershell
python -B scripts\run_model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout.py e\757\解释\model-capability-required-term-pair-readiness-exact-surface-repair-effectiveness-comparison --out-dir e\758\解释\model-capability-required-term-pair-readiness-exact-surface-repair-route-closeout --require-pass --force
```

Playwright 快照确认 HTML 中可见：

- `Status pass`
- `Decision pair_readiness_exact_surface_repair_route_closed`
- `Closed route near_exact_surface_bridge_rows`
- `Next route objective_or_decoding_alternative_plan`
- `Candidates 3`

截图位于：

```text
e/758/图片/v758-exact-surface-repair-route-closeout.png
```

## 证据链角色

v758 是路线收口层。它把“修复路线无效”的比较结果转为后续版本必须遵守的边界，防止项目在同一类无效 rows 上继续消耗版本。

一句话总结：v758 关闭 near-exact surface repair route，并把后续推进明确转向 objective-level 或 decoding-side alternatives。
