# aiproj Elegance Hotspot Closeout v1274

## Program result

E-track 在两版内完成并停止：v1273 建立名称预算机械门；v1274 复核 top-N pin、固定最终 census 并 closeout。计划允许最多三版，不要求凑满。E-A2 没有产生重命名提交，因为 top cohort 中可安全且有意义的候选为 0；这是遵守 pin 边界后的结论，不是遗漏。

## Final census

| Metric | Final value |
|---|---:|
| Python files scanned | 2,049 |
| Historical violations | 7,515 |
| Functions | 3,201 |
| Variables | 2,671 |
| Filenames | 1,610 |
| Fields | 33 |
| New violations | 0 |
| Scan errors | 0 |
| Budget | 40 characters |

`docs/elegance/name-baseline.json` 在最终普通模式运行前后 SHA-256 均为 `4d0f5f9236ef805fc018912c7455724958e8f86763ad6511292b54c739b0e02d`。没有调用 `--update-baseline`，也没有放宽 budget、ruff baseline、mypy floor、coverage floor 或 file-size ratchet。

## Why E-A2 changed no code

名称榜 top 5 全部落在 v1014 publication review 合同：四个 filename 常量决定 `e/1014/解释/review-v1014/` 已归档 sidecar 名；renderer 是该 artifacts 模块 `__all__` 的公开入口；JSON filename 又被 v1015 receipt 模块消费，并沿 v1015-v1021 证据链继续引用。改名会破坏计划明确禁止触碰的 publication/cached-artifact 合同。

scripts 侧有 531 条历史违规，最显眼的是 v1014 与 v1050-v1128 review/build wrappers。它们确实结构相似，但脚本名已进入 `e/<version>/解释/说明.md`、v1130 naming-readability 和后续 code-health evidence。把这些历史 wrapper 批量迁入新 shared engine 会改动被归档命令面，收益低于回归风险。因此没有把“看起来重复”误写成“当前应该重构”。

作为交叉检查，排除明显 publication/science 版本链后最靠前的 promoted-seed handoff receipt 名称也不是安全候选：writer 位于 root public lazy exports，renderers 位于模块 `__all__`，sidecar 文件名已固化在 d/429、d/430、d/456 artifact 中。由此不足以组成五个未 pin 的有意义目标。

## Mechanical evidence

- `python -B scripts/check_name_budget.py --out-dir runs/name-budget-v1274-final`: pass, new 0, blockers 0。
- v1273 final-tree full pytest: 3,759 passed；v1274 不改 Python source。
- v1273 engineering health: all 11 steps pass，mypy 22 targets / 0 diagnostics，CI hygiene 67/67。
- `f/1274/解释/pin-audit.md`: top cohort 与 scripts family 的逐项 pin 证据。
- `f/1274/解释/name-budget/`: 最终 JSON/CSV/Markdown/HTML census。

## Stop decision

E-track 到此停止。后续正常开发由 v1273 gate 阻止新增长名；只有在真实功能改动顺带解除历史 pin、且兼容迁移证据充分时，才更新 shrink-only baseline。不能为了让数字下降去改写冻结 artifact、publication receipt、科学 verdict 或公共兼容入口。

Status: ready for Claude review.
