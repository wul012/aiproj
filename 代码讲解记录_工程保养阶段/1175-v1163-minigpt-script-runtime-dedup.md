# 1175 · v1163 · MiniGPT script_runtime 去重保养

## 本版目标与不做什么

本版是一次契约保持的工程保养，承接 [[1171-v1159-minigpt-train-lm-dedup]] 立下的节奏：每 3-4 个功能版本后做一次纯重构。v1160（RoPE）、v1161（KV-cache）、v1162（长度行为研究）是连续三个功能版本，它们各自在 `scripts/` 下复制了同样的脚手架；本版把其中两段真正逐字节重复的片段抽成共享实现。

明确**不做**：不新增模型能力、不改任何训练超参、不改报告产物结构、不碰 v1156 之前的历史脚本。判定“做得对”的唯一标准是既有测试零改动仍全绿。

## 重复债的事实依据

动手前先用 Grep 数清重复：`def choose_device` 在 `scripts/` 下出现 **14 次**。其中两种变体——v1156–v1162 这 6 个能力线脚本用抛 `SystemExit` 的版本（逐字节一致），8 个历史脚本用抛 `RuntimeError` 的旧版本。另外 `torch.manual_seed/np.random.seed/random.seed` 这组三连 seed 在 v1156/1157/1158/1160/1162 各重复一次。没有测试断言这些函数的异常类型（Grep 确认），所以抽取是安全的。

## 关键修改文件与链路角色

- `src/minigpt/script_runtime.py`（新增）：`choose_device(name)` 解析 `--device`，CUDA 不可用时抛 `SystemExit`（干净 CLI 报错，与 v1156-v1162 行为逐字一致）；`seed_everything(seed)` 一次性 seed torch/numpy/random。
- 6 个能力线脚本迁移：v1156/1157/1158/1160/1162 删除本地 `choose_device`、三连 seed 换成 `seed_everything(...)`、删掉随之不再使用的 `numpy`/`random` 导入；v1161 只迁移 `choose_device`，**保留它原本单独的 `torch.manual_seed`**（它不依赖 numpy/random，套用 `seed_everything` 反而会改变行为，故不套）。
- `tests/test_script_runtime.py`（新增）：cpu/auto 解析、用 mock 让 `torch.cuda.is_available` 返回 False 时 `choose_device("cuda")` 抛 `SystemExit`、`seed_everything` 对三个随机源的可复现性与不同 seed 的差异性。

## 范围边界（诚实声明）

8 个 v1156 之前的历史脚本（train.py、evaluate.py、chat.py、sample_lab.py、eval_suite.py、inspect_*.py）仍各自保留 `choose_device`。它们用的是抛 `RuntimeError("CUDA was requested, ...")` 的旧变体，属不同年代、不同错误契约。本版**故意把它们留在范围外**：迁移它们会把 8 个稳定历史入口的失败模式从 traceback 改成干净退出——虽然更好，但那是行为改变，不该混进一次“契约保持”的保养里。所以 `choose_device` 仍在历史脚本里重复 8 份，这是有意识的取舍，不是漏做。

## 契约保持如何被真实保护

重构版本的“运行证据”就是测试套件：v1156-v1162 的既有模块测试零改动全部通过，证明被迁移脚本所依赖的链路行为没变；全量 `3209 passed`（v1162 的 3203 + 本版 6 个新测试）。此外 6 个迁移脚本 `--help` 全部 exit=0（top-level 导入解析正确），`run_rope_eval_v1160` 的 CPU smoke 实跑 `status=pass`、exit=0，证明共享的 `choose_device`/`seed_everything` 在真实运行链路里工作，而不仅是能 import。

## 一句话总结

v1163 把 6 个能力线脚本重复的 `choose_device` 与 5 处三连 seed 收敛成一个共享 `minigpt.script_runtime`，既有测试零改动全绿、full suite 3209 通过，并诚实地把不同错误契约的历史脚本留在范围外——一次干净的契约保持保养，为下一个长程语料 + NTK/YaRN 能力版本铺好底座。
