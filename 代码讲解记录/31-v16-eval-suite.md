# 31. v16 Eval Suite

这一版新增固定 prompt 评估套件，让不同 checkpoint 可以回答同一组问题，并把结果保存成可比较的 JSON、CSV 和 SVG。

## 文件角色

`data/eval_prompts.json` 保存默认 prompt suite。每个 case 包含：

- `name`
- `prompt`
- `max_new_tokens`
- `temperature`
- `top_k`
- `seed`

`src/minigpt/eval_suite.py` 负责解析 suite、整理生成结果、统计 continuation 长度和不同字符数，并写出报告。

`scripts/eval_suite.py` 是命令行入口，负责加载 checkpoint、tokenizer 和模型，然后逐个 prompt 生成结果。

## 核心流程

```text
checkpoint.pt + tokenizer.json
 -> load_prompt_cases
 -> 每个 PromptCase 设置 seed
 -> model.generate
 -> build_prompt_result
 -> build_eval_suite_report
 -> eval_suite.json / eval_suite.csv / eval_suite.svg
 -> dashboard/playground 展示固定评估产物
```

## 为什么需要它

单个 `generate.py --prompt ...` 只能证明模型能生成。

eval suite 让“生成表现”变成固定流程：同一批 prompt、同一批采样参数、同一批 seed。这样以后比较两个 checkpoint 时，可以看：

- 哪个 run 的 continuation 更长或更多样。
- 哪个 run 在固定 prompt 上更稳定。
- 哪个 run 的输出更适合展示或继续分析。

## 与 sampling lab 的区别

sampling lab 关注“同一个 prompt 下，不同 temperature/top_k/seed 的变化”。

eval suite 关注“同一个 checkpoint 下，一组固定 prompt 的整体表现”。

两个工具互补：前者看采样参数，后者看 checkpoint 在标准问题集上的表现。

## 展示入口

Dashboard 增加 `Eval Suite` 区块，会展示 case 数、平均 continuation 字符数、平均不同字符数和 SVG 图。

Playground 增加 `eval_suite.json`、`eval_suite.csv` 和 `eval_suite.svg` 链接。

## 一句话总结

v16 把“随手试几个 prompt”变成了可以重复运行、可以比较、可以归档的固定评估流程。
