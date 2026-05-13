# 第四十九版代码讲解：benchmark scorecard

## 本版目标、来源和边界

v48 已经把项目成熟度做成 summary，但它回答的是“整个项目成熟到哪里”。v49 的目标更具体：回答“某一次 run 的 benchmark 证据是否完整、质量如何、pair 对比是否稳定”。因此本版新增 benchmark scorecard，把 eval suite、generation quality、pair batch、pair delta stability、evidence completeness 和可选 registry context 合成一份统一评分报告。

本版不重新训练模型，不扩大数据集，不改 eval suite、generation quality 或 pair batch 的原始格式，也不替代 release gate。它只是读取已有产物并生成 run 级评分视图。

## 所在链路

```text
eval suite
 -> generation quality
 -> pair batch / pair delta
 -> run registry context
 -> benchmark scorecard
 -> maturity summary / next roadmap
```

这一层回答的问题是：一个 run 是否有足够的评估覆盖，生成质量是否过关，左右 checkpoint 对比是否稳定，证据文件是否齐全，以及它在 registry 中有没有上下文。

## 关键文件

- `src/minigpt/benchmark_scorecard.py`：构建 scorecard，计算组件分数，合并 case 级行，并渲染 JSON/CSV/Markdown/HTML。
- `scripts/build_benchmark_scorecard.py`：命令行入口，接受 `--run-dir`、`--registry`、`--out-dir` 和 `--title`。
- `tests/test_benchmark_scorecard.py`：用临时 run fixture 覆盖评分组件、registry context、输出文件和 HTML 转义。
- `README.md`：记录 v49 当前能力、tag、截图、学习地图和下一步。
- `b/49/解释/说明.md`：保存本版运行截图解释和 tag 含义。

## 输入数据来源

`build_benchmark_scorecard(run_dir)` 默认读取：

```text
<run-dir>/eval_suite/eval_suite.json
<run-dir>/generation-quality/generation_quality.json
<run-dir>/eval_suite/generation-quality/generation_quality.json
<run-dir>/pair_batch/pair_generation_batch.json
<run-dir>/pair_batch/pair_generation_batch.html
```

如果传入 `registry_path`，还会读取 registry 中的 run count、best-val rank、pair report counts 和 pair delta summary。缺失文件不会让构建直接崩溃，而是进入 `warnings`，同时相应组件会拿到较低分数。

## 评分组件

本版把 scorecard 拆成五个固定组件：

- `eval_coverage`：按 eval suite case 数给分，满分代表固定 prompt 覆盖足够。
- `generation_quality`：按 pass/warn/fail 比例给分，warn 只算半分。
- `pair_consistency`：按 pair batch 中左右生成完全一致的比例给分。
- `pair_delta_stability`：按平均生成字符差距扣分，差距越大说明稳定性越弱。
- `evidence_completeness`：检查 eval、generation quality、pair batch 三组证据文件是否齐全。

最终 `overall_score` 是这些组件的加权平均。当前权重是 eval coverage 0.2、generation quality 0.3、pair consistency 0.2、pair delta stability 0.2、evidence completeness 0.1。

## 输出文件

`write_benchmark_scorecard_outputs` 会写出：

```text
benchmark_scorecard.json
benchmark_scorecard.csv
benchmark_scorecard.md
benchmark_scorecard.html
```

JSON 是完整机器可读报告；CSV 是组件评分表；Markdown 适合讲解和审阅；HTML 适合浏览器截图和作品展示。

## HTML 读法

`benchmark_scorecard.html` 有五块：

- 顶部 stats：整体状态、总分、eval cases、generation quality、pair cases、pair diff、max delta 和 registry rank。
- Benchmark Components：五个组件的状态、分数、权重、加权分和证据说明。
- Case Scores：按 case 合并 eval、generation quality 和 pair comparison 字段。
- Registry Context：展示 run count、best-val rank、pair report counts 和 pair delta 摘要。
- Recommendations / Warnings：把下一步建议和缺失证据集中显示。

这让评审时不需要分别打开 eval suite、generation quality、pair batch 和 registry，先看 scorecard 就能知道 run 的评估状态。

## 测试和证据

本版测试覆盖：

- 组件评分：五个组件都能生成，并计算整体 pass/warn/fail。
- case 合并：同名 case 能合并 eval 字段、generation quality 状态和 pair delta。
- registry context：scorecard 能读取 best-val rank 和 pair delta summary。
- 输出文件：JSON/CSV/Markdown/HTML 都能写出。
- HTML 安全：标题里的 `<...>` 会被转义。

运行证据保存在 `b/49/图片`，包括全量测试、scorecard smoke、结构检查、Playwright Chrome 截图和文档检查。

## 一句话总结

v49 把 MiniGPT 从“有很多分散 benchmark 证据”推进到“一个 run 可以用统一 scorecard 解释评估质量和证据完整性”的阶段。
