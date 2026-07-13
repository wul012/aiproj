# 1235 - v1278 README 展示版：把首页从版本流水变成三十秒展品

## 这一版要解决什么问题

这个仓库的 GitHub 首页在 v1278 之前是给维护者看的，不是给访客看的：README 以文档
索引开头，紧接着是一万两千多行逐版本堆叠的「Current version / Latest checkpoint」
流水账。对维护者和机械门来说这是宝贵的结构——能力节奏检查器逐节解析这些标题——
但对一个第一次点进来的人类访客，三十秒内既看不到这个仓库做过什么科学，也看不到
凭什么相信这些结论。四项目群的 GitHub 展示层改造在 2026-07-13 授权，Node 与
mini-kv 由 codex 各自执行，本仓库按用户指示由评审者直接执行，与 v1277 一样走
完整的车道仪式。

## 先侦察机械面，再动手

README 在这个仓库不是普通文档，动它之前必须清点哪些门在读它。侦察结果决定了整个
改造策略：`model_capability_cadence` 用正则 `^## Latest v(\d+) checkpoint` 逐节
解析 README 并按文件顺序取前十二节判断节奏，所以版本节的标题格式与顺序是机读
接口；`test_project_configuration` 断言根 README 必须含有七个规范化文档的
`(docs/xxx.md)` 链接；`check_project_docs_readability` 要求 README 里的链接目标
全部存在（missing_readme_link_count 必须为零）；`check_model_capability_honest_
measurement` 扫描能力表述的诚实性。结论：**只能做前置插入（prepend-only）**——
在文档索引之前插入展品层，新增标题不得撞上 `## Latest v<数字> checkpoint` 的
正则，既有版本节一字不动。这个侦察步骤本身就是本版最重要的工程决策：如果直接
按「把版本流水移到文末」的直觉做，会当场打断节奏检查器。

## 展品层的信息架构

插入的内容自上而下五层。第一层徽章行：CI 徽章加四枚 shields.io 静态徽章（测试
3,802、覆盖率下限 ≥88.98%、方法=预注册、新命名违规=0），每个数字都有已提交的
来源。第二层「At a glance」双语导语：一段英文一段中文，讲清双车道结构——科学
车道每版一个真问题，工程车道用机械门保证可复现——并且直说「产品不是模型而是
方法」，模型是教学质量这条边界放在导语里而不是藏在角落。第三层「The science
catalog」是整个展品的核心：十三行表格，每行一条已关闭的研究轴——从 LoRA 微调
基础、偏好对齐、蒸馏两部曲、量化悬崖，到 grokking 弧、傅里叶因果回路、校准、
持续学习三部曲、induction 双回路机制、双下降诚实 null、彩票假设失效、叠加涌现、
容量挤压——verdict 逐字引用（`pruning_breaks_circuit`、
`squeeze_hits_capacity_floor` 这些机器判决原样进表），每行给出证据链接。特意在
表格导语里声明：null 与 review 分支和正结果同等排版，因为它们常常是最有教益的
行。第四层「How to trust a result here」把车道方法论压缩成五条：预注册先提交
后运行、CPU 探针先行、多种子否则不算数（列出四次单种子幸运被多种子纠正的版本
号）、缓存零重训字节稳定复推（附两条可以立刻跑的复现命令）、以及十二次抓获的
decide() 阈值 bug 类已成为成文自查步骤。第五层「Boundaries」：toy scale、own
substrate 的 scope 标签，教学质量定位，以及指向 no-promotion boundary 文档的
lookup-only 语义说明。

## 版本节的补账

写版本节时发现并如实披露了一个 v1277 的仪式缺口：v1277 的收尾提交更新了
f/README 与讲解索引，却漏掉了根 README 的「Current version / Latest checkpoint」
两节——节奏检查器于是仍把 v1276 当最新版。本版补上 `## Latest v1277 checkpoint`
（预注册、判决、预算、描述性发现、证据路径五组要点）与本版自己的
`## Latest v1278 checkpoint`，并在 v1278 节里明写这次补账的披露。两节按新在前
的顺序插入 v1276 节之前，保持解析器期望的时间序。

## 验证

聚焦门先行：`test_project_configuration`、`test_project_docs_readability`、
`test_model_capability_cadence`、`test_maturity` 共三十二项全绿；真实仓库上的
`check_project_docs_readability` 报 missing_readme_link_count=0（含两个指向中文
目录的相对链接，GitHub 与检查器都正确解析）；`check_model_capability_honest_
measurement` status=pass。证据归档 `f/1278`：GFM 渲染验证与链接审计记录进解释
目录，首屏渲染截图进图片目录。讲解（本文）先于最终全量测试完成，随后全量
pytest、提交、推送、tag、远端 CI 绿收口。

## 一句话总结

v1278 没有改变任何实验、缓存、判决或门槛——它做的是把这个仓库已经挣到的东西
（十三条轴的诚实判决和一整套可信实验方法）放到访客三十秒能看到的地方，同时用
侦察-约束-前置插入的顺序保证所有机读接口原样存活。
