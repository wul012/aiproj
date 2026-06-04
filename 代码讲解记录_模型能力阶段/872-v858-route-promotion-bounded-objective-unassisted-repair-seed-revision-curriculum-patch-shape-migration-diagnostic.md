# v858：bounded objective curriculum patch shape migration diagnostic

## 本版目标和边界

v858 的目标是把 v853 和 v857 两份真实 replay report 放在一起，对每个 bounded objective case 做逐项比较。

它解决的问题是：v857 的汇总数字看起来和 v853 相同，都是 `any_hit_case_count=2`、`zero_hit_case_count=1`，但 case 级结果已经发生迁移。如果只看汇总，就会误以为 curriculum patch 没有影响；如果只看局部改善，又会误以为能力接近恢复。v858 把这两种误读都挡住。

边界：

- 不训练。
- 不生成文本。
- 不修改 v836 contract。
- 不把 `fixed` partial hit 当作 `fixed loss` recovery。

## 前置链路

```text
v853 seed revision replay comparison
 -> v854 partial-hit diagnostic
 -> v855 curriculum patch
 -> v856 curriculum patch training run
 -> v857 curriculum patch replay comparison
 -> v858 shape migration diagnostic
```

v858 是 v855/v856 是否值得继续扩展训练的前置判断。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic.py`
  - 读取两份 replay report，生成 case-level migration rows、root causes、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration.py`
  - CLI 入口，支持目录或 JSON 文件输入。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic.py`
  - 覆盖迁移诊断、case set mismatch、writer 和 CLI。
- `e/858/解释/bounded-objective-curriculum-patch-shape-migration-diagnostic/`
  - 保存真实 v858 诊断产物。
- `e/858/图片/v858-bounded-objective-curriculum-patch-shape-migration-diagnostic-html.png`
  - Playwright MCP 截图。

## 核心数据结构

每条 `migration_rows` 对应一个 contract case。

主要字段：

```text
case_id
pre_case_pass
post_case_pass
pre_any_hit
post_any_hit
pre_hit_terms
post_hit_terms
pre_missed_terms
post_missed_terms
pre_continuation
post_continuation
migration_class
```

`migration_class` 的含义：

- `improved_to_partial`：post hit term 数量增加，但仍未 pass。
- `regressed_to_zero`：post hit term 数量减少到 zero-hit。
- `stable_partial`：pre/post 都是相同 partial。
- `recovered_case`：post case pass。
- `lost_case`：pre pass 但 post fail。
- `changed_same_hit_count`：命中数量相同但命中项改变。
- `missing_post_case`：post report 缺失对应 case。

## 核心流程

`build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic()` 做四步：

1. 读取 v853/v857 的 `summary` 和 `replay_rows`。
2. 按 `case_id` 对齐，生成 `migration_rows`。
3. 做结构检查：两边 replay 都必须 pass、ready，并且 case id 集合一致。
4. 根据迁移行生成 root causes 和 summary。

结构失败才让 `status=fail`。模型没有恢复只会体现在 `decision` 和 `summary`，不算工具失败。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnosed_profile_sweep_required
case_count=3
improved_case_count=1
regressed_case_count=1
stable_partial_case_count=1
any_hit_case_delta=0
zero_hit_case_delta=0
loss_missed_after_count=3
```

case 级迁移：

```text
canonical_direct_completion -> stable_partial
minimal_direct_completion   -> regressed_to_zero
completion_label_surface    -> improved_to_partial
```

这说明 v855 curriculum patch 不是完全无效，但它把 partial signal 从一个 prompt surface 迁移到另一个 prompt surface，并没有让模型稳定输出 `loss`。

## 路径长度处理

本版真实运行时，最初的超长产物文件名触发 Windows 路径写入失败。修正方式不是绕过错误，而是把证据文件名收敛为：

```text
bounded_objective_curriculum_patch_shape_migration_diagnostic.*
```

这符合当前项目“不要制造难维护巨型文件和难维护巨型命名”的规则。

## 测试覆盖

focused pytest 覆盖：

- v853/v857 典型迁移：1 improved、1 regressed、1 stable partial。
- post report 缺 case 时 `status=fail`。
- JSON/CSV/TXT/Markdown/HTML writer 和 CLI。

```text
3 passed
```

运行证据：

```text
e/858/解释/bounded-objective-curriculum-patch-shape-migration-diagnostic/
e/858/图片/v858-bounded-objective-curriculum-patch-shape-migration-diagnostic-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Improved=1
Regressed=1
Stable partial=1
Any-hit delta=0
Zero-hit delta=0
Loss missed after=3
```

## 一句话总结

v858 把“汇总数字不变”拆成了可解释的 case-level 失败迁移，为下一步 profile sweep 提供了更可靠的依据。
