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

本目录从 v1098 起启用；v1098-v1099 为文档分流批次，不单独新增版本讲解。
