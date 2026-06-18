# v1189：CI unittest portability 修复

## 本版目标和边界

v1189 是一次很小但必要的工程保养版本。它不新增模型能力，不重新训练 v1185 checkpoint，不修改 v1186 的预测 API，不重新解释 v1188 的 Fourier 机制结论。它只处理一个实际阻断：GitHub Actions 从 v1186 开始持续失败，直到 v1188 仍然失败；失败原因不是模型实验错了，而是测试文件对 CI 运行方式的假设错了。

仓库当前 CI 的 Unit tests 入口是 `scripts/run_test_coverage.py`，内部调用 `coverage run -m unittest discover -s tests -v`。这意味着 CI 以 Python 标准库 `unittest` 发现测试文件，并不保证安装 `pytest`。但是 `tests/test_grok_predict_v1186.py` 顶层写了 `import pytest`，只是为了给 shipped checkpoint 集成测试加一个 `pytest.mark.skipif`。这个写法在本地安装了 pytest 的环境里完全正常，却会在 GitHub Actions 的最小测试环境中导入失败。因为失败发生在模块导入阶段，后面的测试根本没有机会运行。

本版边界是：修测试可移植性，而不是给 CI 加 pytest 依赖。给 CI 装 pytest 当然也能让错误消失，但那会把一个单文件测试写法问题扩大成依赖面变化。项目既然已经选择用 stdlib `unittest discover` 做全量 coverage gate，那么测试文件就应该尽量保持 stdlib-compatible。v1189 按这个方向修。

## 失败现象

最新 v1188 main run 的失败日志指向：

```text
Run python -B scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 80
ERROR: test_grok_predict_v1186 (unittest.loader._FailedTest.test_grok_predict_v1186)
ImportError: Failed to import test module: test_grok_predict_v1186
File ".../tests/test_grok_predict_v1186.py", line 10, in <module>
    import pytest
ModuleNotFoundError: No module named 'pytest'
```

这条日志说明两件事。第一，CI 不是在某个断言上失败，而是在 test module import 阶段失败。第二，失败与 v1188 的 interpretability 代码没有直接关系；v1188 只是继承了 v1186 引入的测试导入问题。也就是说，继续改 v1188 的模型代码、FFT 逻辑或者解释文档，都不会修复这个 CI。

## 代码修改

修改集中在 `tests/test_grok_predict_v1186.py`。原文件顶部只有：

```python
import pytest
import torch
```

并在 shipped checkpoint 集成测试前写：

```python
@pytest.mark.skipif(not DEFAULT_CHECKPOINT.exists(), reason="canonical v1185 checkpoint not present")
```

v1189 改成：

```python
import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

并把装饰器改为：

```python
@unittest.skipIf(not DEFAULT_CHECKPOINT.exists(), "canonical v1185 checkpoint not present")
```

这有两个效果。第一，跳过逻辑不再依赖 pytest；即使 CI 环境只有 Python 标准库，也能导入模块。第二，测试文件自己补上 `src/` 路径注入，和仓库很多历史测试文件的模式一致。虽然 `scripts/run_test_coverage.py` 在父进程里插入了 `src`，但它实际启动的是子进程；让测试文件自带路径注入更稳，避免直接用 `unittest` 导入这个模块时找不到 `minigpt`。

## 为什么不改 CI 依赖

这次不把 pytest 加进 CI 依赖，有三个原因。

第一，当前失败只需要 stdlib 替换即可解决。为了一个 skip marker 增加依赖，不符合最小修复原则。

第二，仓库历史全量测试入口已经是 `unittest discover`，很多测试文件虽然以函数形式存在，但 CI 仍会导入它们来做 coverage 和 import hygiene。这个入口的真实契约是“测试模块必须可以被 stdlib unittest 环境导入”。`pytest.mark.skipif` 破坏了这个契约。

第三，未来如果真的要迁移到 pytest，应该作为一个独立测试框架迁移版本来做：更新依赖、CI 命令、测试发现方式、skip/fixture 规则和覆盖率报告。v1189 只是修一处 CI 阻断，不应该顺手改变测试框架。

## 索引修复

本版还顺手修了 `代码讲解记录_工程保养阶段/README.md` 的最近版本索引。目录里已经存在：

- `1197-v1185-minigpt-grokking-checkpoint.md`
- `1198-v1186-minigpt-grokking-checkpoint-inference.md`
- `1199-v1187-minigpt-report-check-common-dedup.md`
- `1200-v1188-minigpt-grokking-interpretability.md`

但是 README 顶部仍停在 `1196-v1184...`。这会让工程保养阶段看起来像 v1185-v1188 没有讲解，实际上只是索引没更新。v1189 将这些条目补回顶部，并新增 `1201-v1189-ci-unittest-portability.md`。这不是新的治理链，只是目录可读性修正。

## 验证方式

本地先跑：

```powershell
python -m py_compile tests\test_grok_predict_v1186.py
```

确认语法可编译。然后用直接导入模拟 CI 的失败阶段：

```powershell
python -B -c "import sys, importlib; sys.path.insert(0, 'tests'); importlib.import_module('test_grok_predict_v1186')"
```

这个命令的重点不是执行函数式测试，而是确认 `unittest discover` 最容易触发的模块导入阶段不再失败。v1188 的 GitHub Actions 正是死在这个阶段：`unittest.loader._FailedTest`。

随后跑 source encoding：

```powershell
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v1189
```

并跑 `git diff --check`，确保没有 BOM、语法错误或空白问题。最终还要推送后观察 main 和 tag 的 GitHub Actions。只要 v1189 的 CI 能通过，就证明 v1186-v1188 连续失败的阻断已经解除。

## 链路角色

v1185 让 checkpoint 可保存；v1186 让 checkpoint 可加载和预测；v1187 把 grokking audit check 的重复脚手架抽到公共模块；v1188 打开机制解释轴。v1189 的角色是把这条线的 CI 重新接上。它没有新能力，但它恢复了项目最基本的工程约束：任何新能力版本必须让 CI 能在干净环境中导入和验证。

一句话总结：v1189 不让模型更强，但它让最近的能力线重新回到可持续交付状态，修掉了一个本地环境掩盖、CI 环境必现的测试依赖错误。
