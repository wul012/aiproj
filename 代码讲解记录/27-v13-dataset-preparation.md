# 27. v13 Dataset Preparation

这一版新增 `src/minigpt/data_prep.py` 和 `scripts/prepare_dataset.py`，把训练数据从“单个 sample 文件”升级为“可准备、可统计、可复用的 corpus”。

## 文件角色

`data_prep.py` 负责发现 `.txt` 文件、规范换行、合并文本、统计来源文件，并导出 `dataset_report.json` 和 `dataset_report.svg`。

`prepare_dataset.py` 是命令行入口：

```powershell
python scripts/prepare_dataset.py data --out-dir runs/dataset
```

它会生成：

- `corpus.txt`
- `dataset_report.json`
- `dataset_report.svg`

## 核心流程

```text
source files / source directories
 -> discover_text_files
 -> normalize_text
 -> build_prepared_dataset
 -> build_dataset_report
 -> write corpus.txt / dataset_report.json / dataset_report.svg
```

## 关键代码

`SourceFileSummary` 保存每个来源文件的字符数、行数、非空行数和不同字符数。

`PreparedDataset` 保存合并后的训练文本和所有来源文件 summary。

`build_dataset_report` 会输出总体字符数、行数、来源文件数、不同字符数和高频字符。这里的 `token_count_char_estimate` 是字符级 tokenizer 下的近似 token 数。

`write_dataset_report_svg` 会画出每个来源文件的字符数条形图，让数据规模差异更容易看出来。

## 训练脚本变化

`scripts/train.py` 新增：

- `--prepared-data`
- `--data-dir`

`--prepared-data` 直接读取 `prepare_dataset.py` 产出的 `corpus.txt`。

`--data-dir` 会在训练前临时合并目录下 `.txt` 文件，并把 `prepared_corpus.txt`、`dataset_report.json`、`dataset_report.svg` 保存进 run 目录。

## 一句话总结

v13 把“模型吃了什么数据”变成明确产物，而不是藏在训练命令背后的一个文件路径。
