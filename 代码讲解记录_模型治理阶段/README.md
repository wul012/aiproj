# MiniGPT 代码讲解记录_模型治理阶段

本目录从 v1098 开始承接 MiniGPT 的模型治理、publication receipt 链路、receipt/index/review/contract-check、文档分流和后续治理收束讲解。

上一阶段 `代码讲解记录_模型能力阶段/` 保留 v473-v1097 的历史讲解，不回头迁移旧文件。

## 写入规则

- 编号继续沿用全局序号，从 `1112-v1098-...` 开始。
- 不是每个版本都必须写代码讲解；轻量文档整理、规则分流、索引维护可以只更新 README 或分流说明。
- 一旦写讲解，必须按仓库规则写清本版目标、明确不做什么、入口/CLI、输出模型、上游证据、核心流程、关键检查、测试覆盖、运行证据和一句话总结。
- 新讲解优先复制 `TEMPLATE.md` 的章节结构，再按本版实际内容删减。
- 对 production readiness、只读报告、上游证据聚合和治理 summary，要参考 `D:\nodeproj\orderops-node\代码讲解记录\107-production-readiness-summary-v3-v103.md` 的写法。

## 当前索引

1140-v1128-publication-receipt-index-review.md
 -> v1128 code explanation: review the v1127 receipt index before the next lookup-only receipt recording.

1139-v1127-publication-receipt-index.md
 -> v1127 code explanation: index the v1125 receipt and v1126 contract check for downstream lookup.

1138-v1126-publication-receipt-check.md
 -> v1126 code explanation: rebuild and contract-check the v1125 lookup-only receipt.

1137-v1125-publication-receipt.md
 -> v1125 code explanation: record the v1124 review as a lookup-only downstream receipt.

1136-v1124-publication-receipt-index-review.md
 -> v1124 code explanation: review the v1123 receipt index before the next lookup-only receipt recording.

1135-v1123-publication-receipt-index.md
 -> v1123 code explanation: index the v1121 receipt and v1122 contract check for downstream lookup.

1134-v1122-publication-receipt-check.md
 -> v1122 code explanation: rebuild and contract-check the v1121 lookup-only receipt.

1133-v1121-publication-receipt.md
 -> v1121 code explanation: record the v1120 review as a lookup-only downstream receipt.

1132-v1120-publication-receipt-index-review.md
 -> v1120 code explanation: review the v1119 receipt index before the next lookup-only receipt recording.

1131-v1119-publication-receipt-index.md
 -> v1119 code explanation: index the v1117 receipt and v1118 contract check for downstream lookup.

1130-v1118-publication-receipt-check.md
 -> v1118 code explanation: rebuild and contract-check the v1117 lookup-only receipt.

1129-v1117-publication-receipt.md
 -> v1117 code explanation: record the v1116 review as a lookup-only downstream receipt.

1128-v1116-publication-receipt-index-review.md
 -> v1116 code explanation: review the v1115 receipt index before the next lookup-only receipt recording.

1127-v1115-publication-receipt-index.md
 -> v1115 code explanation: index the v1113 receipt and v1114 contract check for downstream lookup.

1126-v1114-publication-receipt-check.md
 -> v1114 code explanation: rebuild and contract-check the v1113 lookup-only receipt.

1125-v1113-publication-receipt.md
 -> v1113 code explanation: record the v1112 review as a lookup-only downstream receipt.

1124-v1112-publication-receipt-index-review.md
 -> v1112 code explanation: review the v1111 receipt index before the next lookup-only receipt recording.

1123-v1111-publication-receipt-index.md
 -> v1111 code explanation: index the v1109 receipt and v1110 contract check for downstream lookup.

1122-v1110-publication-receipt-check.md
 -> v1110 code explanation: rebuild and contract-check the v1109 lookup-only receipt.

1121-v1109-publication-receipt.md
 -> v1109 code explanation: record the v1108 review as a lookup-only downstream receipt.

1120-v1108-publication-receipt-index-review.md
 -> v1108 code explanation: review the v1107 receipt index before the next lookup-only receipt recording.

1119-v1107-publication-receipt-index.md
 -> v1107 code explanation: index the v1105 receipt and v1106 contract check for downstream lookup.

1118-v1106-publication-receipt-check.md
 -> v1106 code explanation: rebuild and contract-check the v1105 lookup-only receipt.

1117-v1105-publication-receipt.md
 -> v1105 code explanation: record the v1104 review as a lookup-only downstream receipt.

1116-v1104-publication-receipt-index-review.md
 -> v1104 code explanation: review the v1103 receipt index before the next lookup-only receipt recording.

1115-v1103-publication-receipt-index.md
 -> v1103 code explanation: index the v1101 receipt and v1102 contract check for downstream lookup.

1114-v1102-publication-receipt-check.md
 -> v1102 code explanation: rebuild and contract-check the v1101 lookup-only receipt.

1113-v1101-publication-receipt.md
 -> v1101 code explanation: record the v1100 review as a lookup-only downstream receipt.

1112-v1100-publication-receipt-index-review.md
 -> v1100 code explanation: review the v1097 receipt index before recording the next lookup-only receipt.

本目录从 v1098 起启用；v1098-v1099 为文档分流批次，不单独新增版本讲解。
