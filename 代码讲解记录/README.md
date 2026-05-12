# MiniGPT 代码讲解记录

本目录用于永久记录对 `MiniGPT From Scratch` 项目的分层代码讲解。

讲解风格参考项目根目录下的 `解释代码格式说明`：

```text
先说明文件或类的角色
再给核心流程
然后逐段解释关键代码
最后做一句话总结
```

## 讲解目录

```text
01-tokenizer-and-dataset.md
 -> tokenizer.py / dataset.py：文本如何变成训练样本

02-model-core.md
 -> model.py：GPTConfig、CausalSelfAttention、Block、MiniGPT 和自回归生成

03-train-generate.md
 -> scripts/train.py / scripts/generate.py：训练循环、checkpoint 保存和文本生成入口

04-tests-docs.md
 -> tests、README、a/1 归档：如何证明项目能跑、能讲清楚、能继续迭代

05-v2-training-artifacts.md
 -> history.py、plot_history.py、train.py v2：训练历史、loss 曲线、样例输出和 resume

06-version-2-tests-docs.md
 -> v2 测试、README、a/2 归档和版本说明更新

07-v3-bpe-tokenizer.md
 -> BPETokenizer、load_tokenizer、inspect_tokenizer.py：从字符级走向子词合并

08-version-3-tests-docs.md
 -> v3 BPE smoke、README、a/3 归档和 tag 说明

09-v4-attention-inspection.md
 -> model.py attention capture、inspect_attention.py：导出 causal attention JSON/SVG

10-version-4-tests-docs.md
 -> v4 attention smoke、README、a/4 归档和 tag 说明

11-v5-prediction-evaluation.md
 -> prediction.py、inspect_predictions.py、evaluate.py：查看 next-token 概率和 checkpoint perplexity

12-version-5-tests-docs.md
 -> v5 prediction/evaluation smoke、README、a/5 归档和 tag 说明

13-v6-chat-wrapper.md
 -> chat.py、scripts/chat.py：把基础语言模型包装成简易对话入口

14-version-6-tests-docs.md
 -> v6 chat smoke、README、a/6 归档和 tag 说明

15-v7-model-report.md
 -> model_report.py、inspect_model.py：导出模型结构、参数量和关键张量形状

16-version-7-tests-docs.md
 -> v7 model report smoke、README、a/7 归档和 tag 说明

17-v8-dashboard.md
 -> dashboard.py、build_dashboard.py：把实验产物汇总成静态 HTML 报告

18-version-8-tests-docs.md
 -> v8 dashboard smoke、README、a/8 归档和 tag 说明

19-v9-run-comparison.md
 -> comparison.py、compare_runs.py：横向比较多个 MiniGPT 实验 run

20-version-9-tests-docs.md
 -> v9 comparison smoke、README、a/9 归档和 tag 说明

21-v10-sampling-lab.md
 -> sampling.py、sample_lab.py：比较不同 temperature/top_k/seed 下的生成结果

22-version-10-tests-docs.md
 -> v10 sampling smoke、README、a/10 归档和 tag 说明

23-v11-playground-ui.md
 -> playground.py、build_playground.py：生成本地静态 Playground Web UI

24-version-11-tests-docs.md
 -> v11 playground smoke、README、a/11 归档和 tag 说明

25-v12-playground-server.md
 -> server.py、serve_playground.py：给 Playground 增加本地 HTTP 生成接口

26-version-12-tests-docs.md
 -> v12 server smoke、README、a/12 归档和 tag 说明

27-v13-dataset-preparation.md
 -> data_prep.py、prepare_dataset.py：合并文本语料并导出 dataset report

28-version-13-tests-docs.md
 -> v13 dataset smoke、README、a/13 归档和 tag 说明

29-v14-run-manifest.md
 -> manifest.py、train.py、dashboard.py、playground.py：记录训练 run 的复现元数据与产物索引

30-v15-dataset-quality.md
 -> data_quality.py、data_prep.py、train.py：生成 dataset fingerprint 和轻量数据质量报告

31-v16-eval-suite.md
 -> eval_suite.py、scripts/eval_suite.py、data/eval_prompts.json：固定 prompt 评估套件

32-v17-run-registry.md
 -> registry.py、scripts/register_runs.py：索引多个 run 的 manifest、数据指纹、质量状态和 eval suite

33-v18-registry-html.md
 -> registry.py、scripts/register_runs.py、test_registry.py：把 run registry 从机器可读 JSON/CSV/SVG 扩展到可浏览 HTML 报告

34-v19-registry-interactions.md
 -> registry.py、test_registry.py、playwright_chrome_smoke.ps1：给 registry.html 增加搜索、质量筛选、排序和浏览器验证

35-v20-registry-saved-views.md
 -> registry.py、test_registry.py：给 registry.html 增加 URL 视图状态、分享链接和当前可见行 CSV 导出

36-v21-registry-annotations.md
 -> registry.py、register_runs.py、test_registry.py：读取 run_notes.json，把 notes/tags 纳入 registry JSON/CSV/SVG/HTML
37-v22-registry-leaderboards.md
 -> registry.py、register_runs.py、test_registry.py：给 registry 增加 best-val 排名、loss delta 和 HTML leaderboard
38-v23-experiment-cards.md
 -> experiment_card.py、build_experiment_card.py、dashboard.py、playground.py、registry.py：把单个 run 汇总成 JSON/Markdown/HTML 实验卡
39-v24-model-cards.md
 -> model_card.py、build_model_card.py、test_model_card.py：把 registry 和多张 experiment card 汇总成项目级模型卡
40-v25-project-audit.md
 -> project_audit.py、audit_project.py、test_project_audit.py：给 registry/model card 增加 pass/warn/fail 项目审计门禁
41-v26-release-bundle.md
 -> release_bundle.py、build_release_bundle.py、test_release_bundle.py：把 registry、model card 和 audit 汇总成 release evidence bundle
```

## 项目整体理解

`MiniGPT From Scratch` 是一个 PyTorch 编写的字符级 GPT 学习项目。

它的核心链路是：

```text
中文文本
 -> prepare_dataset.py 合并多个 .txt 来源
 -> CharTokenizer 或 BPETokenizer encode
 -> token id 序列
 -> model report 可检查参数量和张量形状
 -> get_batch 采样 x/y
 -> MiniGPT.forward
 -> attention capture 可选记录每层注意力矩阵
 -> logits
 -> top-k next-token predictions / perplexity
 -> eval_suite.json/csv/svg 固定 prompt 生成评估
 -> cross entropy loss
 -> AdamW 更新参数
 -> metrics.jsonl / loss_curve.svg / sample.txt
 -> dataset_report.json/svg 记录语料来源和规模
 -> dataset_quality.json/svg 记录语料指纹、重复和质量提示
 -> run_manifest.json/svg 记录代码、环境、数据、配置、指标和产物索引
 -> generate 自回归采样新 token
 -> chat prompt 包装多轮消息
 -> dashboard.html 汇总实验产物
 -> comparison.json/csv/svg 横向比较多个 run
 -> sample_lab.json/csv/svg 比较采样参数
 -> playground.html 组合 prompt 控件、命令片段和 artifact 链接
 -> /api/generate 本地调用 checkpoint 生成
 -> registry.json/csv/svg 索引多个实验 run
 -> registry.html 在浏览器里浏览、搜索、筛选、排序、分享和导出多个 run、notes、tags、质量状态、best-val 排名、loss delta 和 artifact 链接
 -> experiment_card.json/md/html 汇总单个 run 的状态、数据、训练、评估、registry 排名和建议
 -> model_card.json/md/html 汇总整个实验系列的最佳 run、coverage、limitations 和后续建议
 -> project_audit.json/md/html 检查实验系列是否满足 release-style review 的基本门禁
 -> release_bundle.json/md/html 汇总最终交付证据、审计状态、top runs 和 artifact 链接
 -> tokenizer.decode
 -> 生成文本
```

一句话理解：这个项目用最小的工程结构复现 GPT 的核心训练目标，也就是“根据前文预测下一个 token”，再逐步补上观察、评估和对话包装这些应用层能力。
