# MiniGPT 代码讲解记录_评估基准阶段

本目录从 v35 开始记录 MiniGPT 的“评估基准阶段”。上一阶段 `代码讲解记录_发布治理阶段` 已经把 v31-v34 的 release gate profiles、profile comparison、profile deltas 和 configurable baseline 收口；v35-v36 开始，项目重点从“发布治理继续细分”转向“模型能力如何被固定任务集和稳定数据版本比较”。

## 写入规则

新版本如果主要围绕 benchmark、标准评估集、模型能力横向比较、数据版本和推理服务评估，就写入本目录。编号继续沿用全局顺序：

```text
50-v35-benchmark-eval-suite.md
51-v36-dataset-versioning.md
```

说明文档继续向参考文档靠齐：

```text
D:\C\mini-kv\代码讲解记录\111-restart-recovery-evidence-v55.md
```

也就是每篇要写清楚：

- 本版目标、来源、边界和不做什么。
- 本版位于模型能力评估链路的哪一环。
- 关键文件、字段语义、输入输出和运行流程。
- JSON、CSV、SVG、HTML、截图和归档为什么能作为证据。
- 测试覆盖链路、关键断言和失败时能拦住什么。
- 一句话总结项目成熟度推进到了哪一层。

## 当前项目进度基线

截至 v36，项目已经具备从训练、数据治理、数据版本、实验记录、发布治理到 benchmark prompt suite 的完整学习型 AI 工程链路。发布治理已经能解释 profile 分歧；评估基准阶段开始回答更直接的问题：

```text
同一个 checkpoint 在固定任务集上表现如何？
同一个 checkpoint 到底用了哪个 dataset version？
不同 checkpoint、tokenizer、模型大小和训练步数以后能否横向比较？
```

当前评估主线：

```text
eval prompts
 -> benchmark prompt metadata
 -> dataset version manifest
 -> eval suite JSON/CSV/SVG/HTML
 -> generation quality analysis
 -> registry / dashboard / playground artifact links
 -> later baseline model comparison
```

## 后续讲解索引

```text
50-v35-benchmark-eval-suite.md
 -> 第三十五版代码讲解：把 fixed prompt eval suite 升级成带任务类型、难度、预期行为和 HTML 报告的 benchmark prompt suite
51-v36-dataset-versioning.md
 -> 第三十六版代码讲解：给 prepared corpus 增加 dataset id、version manifest、HTML 报告和下游 artifact 链路
```

后续推进 v37 时，在这里继续追加 `52-v37-主题.md`。

## 一句话总览

本目录记录 MiniGPT 从“证据链很完整”转向“模型能力可以被固定任务集和稳定数据版本比较”的过程。
