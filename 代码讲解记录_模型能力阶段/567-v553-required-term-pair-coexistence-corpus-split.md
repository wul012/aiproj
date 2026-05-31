# v553 required-term pair coexistence corpus split 代码讲解

## 本版目标和边界

v552 新增 `equals_surface_fixed_repair` 后，`model_capability_required_term_pair_coexistence_refresh.py` 达到 488 行，已经接近项目“500-800 行需要拆分”的维护阈值。v553 的目标是把 corpus 设计从训练执行文件里拆出去，避免下一次能力实验继续推高单文件复杂度。

本版不改变训练参数、不重新训练、不改变任何已有 corpus 文本。它是 contract-preserving refactor：调用方仍然可以从 `model_capability_required_term_pair_coexistence_refresh` 导入 `PAIR_COEXISTENCE_CORPUS_MODES` 和 `build_pair_coexistence_refresh_corpus`。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 新模块，专门放 corpus mode 枚举、corpus builder 和 prompt surface helper。
  - 每个 corpus mode 拆成 `_extend_*()` 小函数，后续新增 mode 时不需要改训练执行逻辑。
- `src/minigpt/model_capability_required_term_pair_coexistence_refresh.py`
  - 删除原本的大型 corpus builder。
  - 从 corpus 模块导入并 re-export 对外名字。
  - `_source_report()` 改为调用 `source_prompts(corpus_mode)`。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 原有测试保持不变，继续证明旧导入路径可用。

## 拆分前后职责

拆分前：

```text
coexistence_refresh.py
  - 训练命令
  - replay source report
  - summary / decision
  - corpus mode 枚举
  - 五种 corpus 文本生成
  - equals surface prompt 选择
```

拆分后：

```text
coexistence_refresh.py
  - 训练命令
  - replay source report
  - summary / decision

coexistence_corpus.py
  - corpus mode 枚举
  - corpus 文本生成
  - prompt surface 选择
```

这让“训练怎么跑”和“训练样本怎么写”分开，后续修复 loss 分支时风险更低。

## 行数变化

```text
model_capability_required_term_pair_coexistence_refresh.py: 488 -> 306
model_capability_required_term_pair_coexistence_corpus.py: 219
```

两个文件都低于 500 行，且职责更窄。

## 测试覆盖

测试覆盖仍来自既有 refresh/stability 测试：

- spaced answer corpus 仍包含 `fixed: fixed` / `loss: loss`。
- colon-immediate corpus 仍无空格。
- first-token boost、isolated prompt、loss-calibrated、equals repair mode 都保持原断言。
- `equals_surface_fixed_repair` 仍 replay `fixed=` / `loss=`。
- stability runner 仍能通过 `PAIR_COEXISTENCE_CORPUS_MODES` 识别 CLI choices。

这些断言证明拆分没有改变外部行为。

## 归档角色

`e/553` 保存拆分说明、截图和验证记录。它不是模型能力新结论，而是为了让 v554 之后的能力实验更容易维护。

一句话总结：v553 把 required-term pair 的 corpus 设计从训练执行文件中分离出来，给后续 loss-preserving repair 留出干净边界。
