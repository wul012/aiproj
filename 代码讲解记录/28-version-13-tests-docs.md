# 28. v13 测试、文档和归档

这一篇记录 v13 的验收材料：数据准备测试、prepared-data 训练 smoke、README 更新、`a/13` 截图归档和版本标签说明。

## 新增测试

`tests/test_data_prep.py` 覆盖：

- 换行和尾部空白规范化
- 从目录中发现 `.txt` 文件
- 多文件合并成 prepared dataset
- 生成 dataset report
- 写出 `corpus.txt`、`dataset_report.json`、`dataset_report.svg`

## smoke 验证

v13 smoke 会准备两个临时文本文件：

```text
tmp/v13-dataset-smoke/raw/part1.txt
tmp/v13-dataset-smoke/raw/part2.txt
```

然后运行：

```powershell
python scripts/prepare_dataset.py tmp/v13-dataset-smoke/raw --out-dir tmp/v13-dataset-smoke/prepared
python scripts/train.py --prepared-data tmp/v13-dataset-smoke/prepared/corpus.txt --out-dir tmp/v13-dataset-smoke/run ...
```

最后检查 dataset report、训练产物、dashboard/playground 链接是否存在。

## 截图归档

`a/13/图片` 保存五张关键截图：

- `01-unit-tests.png`
- `02-prepare-dataset.png`
- `03-train-prepared-data.png`
- `04-dataset-artifacts-check.png`
- `05-docs-check.png`

`a/13/解释/说明.md` 对每张截图做简短说明。

## 版本标签

v13 使用 `v13.0.0` 标签。标签说明应概括 dataset preparation、prepared-data training、dataset reports、测试和截图归档。

## 一句话总结

v13 的验收重点是“数据准备 -> 数据报告 -> prepared corpus 训练 -> 产物可视化入口”这条链路已经打通。
