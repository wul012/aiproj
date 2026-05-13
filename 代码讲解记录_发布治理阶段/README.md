# MiniGPT 代码讲解记录_发布治理阶段

本目录从 v31 开始作为新的代码讲解入口使用，和旧目录同级。

旧目录保留 v1-v30 的历史讲解，不做迁移；后续新版本默认写入本目录。这样既不把 45 篇已有记录拆散，也能避免未来所有版本继续堆在一个文件夹里。

```text
D:\aiproj\代码讲解记录
D:\aiproj\代码讲解记录_发布治理阶段
```

## 写入规则

后续每次推进 MiniGPT 版本时，新的代码讲解文件写入本目录，编号继续沿用旧目录的全局顺序：

```text
46-v31-主题.md
47-v32-主题.md
48-v33-主题.md
```

如果项目以后进入新的大阶段，再新建同级目录，不继续塞进当前阶段目录。目录命名格式为：

```text
代码讲解记录_阶段名称
```

示例：

```text
代码讲解记录_发布治理阶段
代码讲解记录_训练规模化阶段
代码讲解记录_多项目融合阶段
```

说明文档结构继续向下面这篇参考文档靠齐：

```text
D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md
```

也就是说，本目录不只写“代码做了什么”，还要写清楚：

- 本版目标、来源、边界和明确不做什么。
- 本版处在发布治理阶段的哪一环。
- 关键文件、字段语义、输入输出和运行流程。
- JSON、Markdown、HTML、SVG、截图、归档为什么能作为证据。
- 测试覆盖链路、关键断言和失败时能拦住什么。
- 一句话总结本版把项目成熟度推进到哪一层。

## 当前项目进度基线

截至 v34，项目已经从 MiniGPT 教学雏形推进到带实验记录、数据质量、评估套件、registry、experiment card、model card、project audit、release bundle、release gate、generation quality policy、release gate policy profiles、profile comparison report、profile delta explanations 和 configurable delta baseline 的学习型 AI 工程。

当前主线能力：

```text
模型核心
 -> tokenizer / dataset
 -> MiniGPT causal self-attention
 -> train / generate / chat
 -> checkpoint / metrics / loss curve

实验治理
 -> dataset preparation
 -> dataset quality
 -> run manifest
 -> eval suite
 -> run registry
 -> experiment card
 -> model card

发布证据链
 -> project audit
 -> release bundle
 -> release gate
 -> generation quality analysis
 -> generation quality audit chain
 -> release gate generation-quality policy
 -> release gate policy profiles
 -> release gate profile comparison
 -> release gate profile delta explanations
 -> configurable release gate delta baseline
```

成熟度判断：

```text
GPT 原理学习：较完整
实验复现与索引：中高成熟
发布证据链：进入可按策略视角解释分歧的发布治理阶段
真实大模型能力：仍不是目标
真实生产训练系统：仍需继续补强
```

还没有完成的方向：

```text
profile-delta 严重度分组/筛选
更稳定的质量阈值配置
更完整的实验对比基准
更强的数据治理和数据卡
训练规模化与设备适配
跨项目证据链融合
```

## 后续讲解索引

新版本讲解从这里继续追加：

```text
46-v31-release-gate-policy-profiles.md
 -> 第三十一版代码讲解：把 release gate 的单点参数升级成 standard/review/strict/legacy 策略档位
47-v32-release-gate-profile-comparison.md
 -> 第三十二版代码讲解：把多个 policy profile 的 gate 结果汇总成 JSON/CSV/Markdown/HTML 对比矩阵
48-v33-release-gate-profile-deltas.md
 -> 第三十三版代码讲解：解释 compared profile 相对 baseline profile 新增或移除了哪些 failed/warned checks
49-v34-configurable-release-gate-baseline.md
 -> 第三十四版代码讲解：让 profile deltas 可以显式选择 baseline profile
```

v31-v34 的发布治理阶段到 `49-v34-configurable-release-gate-baseline.md` 先收口。v35 开始转入评估基准阶段，新的讲解记录写入同级目录：

```text
代码讲解记录_评估基准阶段/
50-v35-benchmark-eval-suite.md
```

从 v32 起，运行截图和解释归档不再继续写入 `a/`，而是写入与 `a/` 同级的 `b/`：

```text
b/<version>/图片
b/<version>/解释/说明.md
```

## 一句话总览

旧目录记录“MiniGPT 如何从零长到 v30 的完整学习和证据链历史”，本目录从 v31 开始继续记录“每版如何把发布治理、质量门禁和可复查交付做得更明确”。
