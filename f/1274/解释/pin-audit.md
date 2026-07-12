# v1274 E-A2 Top-N Pin Audit

## 判定口径

E-A2 只允许重命名“未被 schema、artifact path、registry、publication receipt、cached artifact、`decide()` 合同或公共兼容入口固定”的名称。只要存在一项 pin，就不进入改名集合。审计不以“仓库内可批量替换”为安全证明，因为历史 artifact 与仓库外消费者不受一次 `rg` 替换保护。

## Top 5

| Rank | Kind / length | Candidate | Pin evidence | Decision |
|---|---:|---|---|---|
| 1 | variable / 210 | v1014 Markdown filename constant | 值对应 `e/1014/解释/review-v1014/*.md` 的真实归档文件；由 artifacts writer 消费 | pinned |
| 2 | function / 208 | v1014 Markdown renderer | 位于 artifacts `__all__`，由 v1014 contract test 直接导入；生成上述 publication sidecar | pinned |
| 3 | variable / 206 | v1014 HTML filename constant | 值对应 `e/1014/解释/review-v1014/*.html` | pinned |
| 4 | variable / 206 | v1014 JSON filename constant | 被 v1015 receipt 模块直接导入；v1015-v1021 归档证据继续引用 v1014 stem | pinned |
| 5 | variable / 206 | v1014 text filename constant | 值对应 `e/1014/解释/review-v1014/*.txt` | pinned |

完整长名保留在 `f/1274/解释/name-budget/name_budget.json` 的 `top_offenders` 中，本表不复制 200 字符标识符，避免审计文档自身变得不可读。

## 下游与归档事实

- v1014 stem 在源代码、测试、scripts 与 e/1014-e/1021 证据中有 46 个文件级命中。
- v1014 目录实际保存 CSV、HTML、JSON、Markdown、text 五种同 stem sidecar。
- v1015 源模块直接导入 v1014 JSON filename 常量，并以其定位 source review。
- v1014 renderer 与 writer 由测试作为公开入口直接导入；兼容别名会继续保留超长公开名称，动态字符串绕门则属于明确的 gate gaming。

## scripts duplication family

scripts census 有 531 条超预算项。最长 family 是 review/build receipt-index wrappers：v1014 的脚本名长度 195，v1050-v1128 多个 review wrapper 长度 186。抽样脚本结构确实重复，但路径已经写入 e/1050、e/1054、f/1130 naming-readability 与 f/1266 code-health evidence。它们是历史可复现命令面，不是当前 active CLI family；本版不改。

## 交叉候选

排除明显 publication/science version chain 后，靠前的是 promoted-seed handoff receipt contract summary check。其 writer 位于 `_root_public_exports.py` 和 `_root_lazy_exports_core.py`，renderers 位于模块 `__all__`，sidecar 路径已进入 d/429、d/430、d/456。仍为 pinned，不能凑成五个安全目标。

## 结论

`eligible_meaningful_top_count=0`。E-A2 按计划跳过代码改动，不更新 baseline；E-A3 直接复核最终 census 并 closeout。
