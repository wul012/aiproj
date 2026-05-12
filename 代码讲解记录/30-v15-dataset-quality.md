# 30. v15 Dataset Quality

这一版新增 `src/minigpt/data_quality.py`，把 v13 的 dataset report 往前推进一步：不仅知道语料有多大、来自哪里，还能知道它的稳定指纹和基础质量风险。

## 文件角色

`data_quality.py` 负责生成两类产物：

- `dataset_quality.json`：机器可读的质量报告。
- `dataset_quality.svg`：人可以快速查看的质量摘要图。

`data_prep.py` 现在会给合并后的 corpus 和每个 source 文件计算 `sha256`，并在 `write_prepared_dataset` 时一并写出质量报告。

`train.py` 会在 `--data-dir` 训练时生成质量报告，也会在 `--prepared-data` 训练时复制已有质量报告。

## 核心流程

```text
source .txt files
 -> build_prepared_dataset
 -> corpus fingerprint / source sha256
 -> build_dataset_quality_report
 -> dataset_quality.json
 -> dataset_quality.svg
 -> train/dashboard/playground/manifest 引用质量产物
```

## 关键检查

`build_dataset_quality_report` 会检查：

- 总字符数是否过少。
- 不同字符比例是否过低。
- source 文件是否为空或过短。
- source 文件内容是否重复。
- 规范化后的长行是否重复出现。

这些检查不是为了“一票否决”训练，而是为了让训练前的数据风险可见。

## 指纹意义

`fingerprint` 是合并后 corpus 的 SHA-256。只要语料内容变了，fingerprint 就会变。

这让后续实验比较更可靠：两个 run 如果 loss 不同，可以先看模型参数、seed、代码版本，再看 dataset fingerprint 是否一致。

## 展示入口

Dashboard 增加了 dataset quality 状态、短指纹和 SVG 图。

Playground 增加了 `dataset_quality.json` 和 `dataset_quality.svg` 链接。

Run manifest 的 `data.dataset_quality` 会保存质量摘要，方便未来做实验注册表。

## 一句话总结

v15 把“这份语料是不是同一份、有没有明显质量风险”变成了可记录、可追踪的工程产物。
